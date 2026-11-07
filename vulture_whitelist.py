from __future__ import annotations

# vulture matches an entry by its bare name, so one entry silences every report of that name
# in the tree: the family's dead-code gate checks each entry still answers a report, and the
# names are listed one by one, since a blanket all-caps exemption once hid a token nobody
# imported.
_.paintEvent
_.nextCheckState
_.mouseMoveEvent
_.mouseReleaseEvent
_.eventFilter

pytest_plugins
pytestmark

MESSAGE_TYPE_SIZE
MESSAGE_PAD_V
MESSAGE_PAD_H
MESSAGE_RADIUS
MESSAGE_TOP_MARGIN

SIZES
