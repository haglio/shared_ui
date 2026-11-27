from __future__ import annotations

from app_support.pcloud.api import PCloudRefused
from app_support.pcloud.sign_in import Say, SignedIn, SignInSteps
from PySide6.QtWidgets import QApplication

from shared_ui.pcloud_sign_in import SignInWindow


def _window(steps: SignInSteps, answers: list, signed: list[str]) -> SignInWindow:
    QApplication.instance() or QApplication([])
    return SignInWindow(steps, signing_in=lambda *_asked: answers.pop(0), sending_a_code=lambda _by_sms: Say("Code sent by SMS."),
                        signed_in=signed.append)


def test_it_asks_for_the_pcloud_email_and_password_alone_until_pcloud_asks_for_a_code():
    window = _window(SignInSteps(), [], [])

    assert (window.code.isHidden(), window.by_sms.isHidden(), window.log_in.isEnabled()) == (True, True, False)


def test_a_sign_in_pcloud_takes_keeps_the_login_and_closes_the_window():
    signed: list[str] = []
    window = _window(SignInSteps(), [SignedIn("made-up-login")], signed)
    window.email.setText("jane@example.test")
    window.password.setText("made up secret")

    window.log_in.click()

    assert (signed, window.result()) == (["made-up-login"], SignInWindow.DialogCode.Accepted)


def test_a_challenge_shows_the_code_box_the_send_buttons_and_what_pcloud_said():
    steps = SignInSteps()
    window = _window(steps, [], [])
    said = steps.refused(PCloudRefused("login", 2297, "made-up", token="made-up-challenge", has_devices=False), steps.attempt(""))
    window.email.setText("jane@example.test")
    window.password.setText("made up secret")

    window.say(said)

    assert (window.code.isHidden(), window.by_sms.isHidden(), window.to_other_apps.isEnabled(), window.problem.text()) == (
        False, False, False, said.words)
