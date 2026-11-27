from __future__ import annotations

import sys
import time
from collections.abc import Callable

from app_support.pcloud.api import PCloud, PCloudRefused
from app_support.pcloud.library import LOGIN_FILE
from app_support.pcloud.sign_in import Say, SignedIn, SignInSteps, save_login, sign_in
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout

from shared_ui import colors, running_copy, spacing
from shared_ui.application import application

PCLOUDS_API = "api.pcloud.com"
_ITS_RUNNING_COPY = "haglio-pcloud-sign-in"
_A_RUNNING_COPY_ANSWERS_WITHIN_S = 2.0


class SignInWindow(QDialog):
    def __init__(self, steps: SignInSteps, *, signing_in: Callable[[str, str, str], SignedIn | Say],
                 sending_a_code: Callable[[bool], Say], signed_in: Callable[[str], None]) -> None:
        super().__init__()
        self.setWindowTitle("Log in to pCloud")
        self._steps, self._signing_in, self._sending_a_code, self._signed_in = (
            steps, signing_in, sending_a_code, signed_in)
        self.email = QLineEdit(placeholderText="pCloud email")
        self.password = QLineEdit(placeholderText="pCloud password", echoMode=QLineEdit.EchoMode.Password)
        self.code = QLineEdit(placeholderText="Verification or recovery code")
        self.by_sms = QPushButton("Send code by SMS")
        self.to_other_apps = QPushButton("Send code to your other pCloud apps")
        self.log_in = QPushButton("Log in")
        self.problem = QLabel(wordWrap=True)
        self.problem.setStyleSheet(f"color: {colors.RED.name()}")
        column = QVBoxLayout(self)
        column.setContentsMargins(*[spacing.MARGIN_DIALOG] * 4)
        column.setSpacing(spacing.GAP_DIALOG)
        for part in (self.email, self.password, self.code, self.by_sms, self.to_other_apps, self.log_in, self.problem):
            column.addWidget(part)
        for box in (self.email, self.password):
            box.textChanged.connect(self._show_what_the_steps_want)
        self.log_in.clicked.connect(self._log_in)
        self.by_sms.clicked.connect(lambda: self.say(self._sending_a_code(True)))
        self.to_other_apps.clicked.connect(lambda: self.say(self._sending_a_code(False)))
        self._show_what_the_steps_want()

    def say(self, said: Say) -> None:
        self.problem.setText(said.words)
        self._show_what_the_steps_want()

    def _show_what_the_steps_want(self) -> None:
        challenged = self._steps.challenge_token is not None
        self.code.setHidden(not self._steps.wants_code)
        self.by_sms.setHidden(not challenged)
        self.to_other_apps.setHidden(not challenged)
        self.to_other_apps.setEnabled(self._steps.can_send_code_to_other_apps)
        self.log_in.setEnabled(bool(self.email.text() and self.password.text()))

    def _log_in(self) -> None:
        answer = self._signing_in(self.email.text(), self.password.text(), self.code.text())
        if isinstance(answer, SignedIn):
            self._signed_in(answer.auth)
            self.accept()
            return
        self.say(answer)


def _sending_a_code(pcloud: PCloud, steps: SignInSteps) -> Callable[[bool], Say]:
    def send(by_sms: bool) -> Say:
        try:
            pcloud.send_second_factor_code(steps.challenge_token or "", by_sms=by_sms)
        except PCloudRefused as refusal:
            return Say(str(refusal))
        return Say("Code sent by SMS." if by_sms else "Code sent — check the pCloud app on your other machines.")

    return send


def main(argv: list[str] | None = None) -> int:
    with application(argv or sys.argv):
        if running_copy.ask(_ITS_RUNNING_COPY, b"show", until=time.monotonic() + _A_RUNNING_COPY_ANSWERS_WITHIN_S):
            return 0
        pcloud, steps = PCloud(PCLOUDS_API, auth=""), SignInSteps()
        window = SignInWindow(
            steps, signing_in=lambda email, password, code: sign_in(pcloud, steps, email, password, code),
            sending_a_code=_sending_a_code(pcloud, steps),
            signed_in=lambda auth: save_login(LOGIN_FILE, api_host=PCLOUDS_API, auth=auth))
        listening = running_copy.listen(_ITS_RUNNING_COPY, lambda _said, reply: (window.raise_(), reply(b"shown")))
        try:
            return 0 if window.exec() == QDialog.DialogCode.Accepted else 1
        finally:
            listening.close()


if __name__ == "__main__":
    sys.exit(main())
