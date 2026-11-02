from __future__ import annotations

from shared_ui import message_shape, notice_shape


def test_the_old_name_says_what_the_new_one_says_until_the_apps_have_moved():
    assert (notice_shape.NOTICE_PAD_H, notice_shape.NOTICE_PAD_V, notice_shape.NOTICE_RADIUS,
            notice_shape.NOTICE_TOP_MARGIN, notice_shape.NOTICE_TYPE_SIZE) == (
        message_shape.MESSAGE_PAD_H, message_shape.MESSAGE_PAD_V, message_shape.MESSAGE_RADIUS,
        message_shape.MESSAGE_TOP_MARGIN, message_shape.MESSAGE_TYPE_SIZE)
