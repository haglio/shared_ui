from __future__ import annotations

# vulture matches an entry by its bare name, so one entry silences every report of that name
# in the tree: the family's dead-code gate checks each entry still answers a report, and the
# names are listed one by one, since a blanket all-caps exemption once hid a token nobody
# imported.
# FlowLayout's set_group_spacing and placed_from_since are called by Origenerator's gallery
# buttons and tiles-in-sight code; expandingDirections is called by Qt.
_.paintEvent
_.nextCheckState
_.mouseMoveEvent
_.mouseReleaseEvent
_.eventFilter
_.expandingDirections
_.set_group_spacing
_.placed_from_since

pytest_plugins
pytestmark


SIZES
