from typing import List

from blupee.models.event import Event


def get_test_prefix() -> List[Event]:
    # get a test prefix
    return [
        Event(
            id=3680001,
            activity="A_SUBMITTED",
            start_timestamp=0,
            end_timestamp=0,
            resource="User_1",
            attributes={},
        ),
        Event(
            id=3680002,
            activity="A_PARTLYSUBMITTED",
            start_timestamp=0,
            end_timestamp=0,
            resource="User_1",
            attributes={},
        ),
        Event(
            id=3680003,
            activity="A_PREACCEPTED",
            start_timestamp=0,
            end_timestamp=0,
            resource="User_1",
            attributes={},
        ),
        Event(
            id=3680004,
            activity="W_Completeren aanvraag",
            start_timestamp=0,
            end_timestamp=0,
            resource="User_1",
            attributes={},
        ),
        Event(
            id=3680005,
            activity="W_Completeren aanvraag",
            start_timestamp=0,
            end_timestamp=0,
            resource="User_1",
            attributes={},
        ),
        Event(
            id=3680006,
            activity="W_Completeren aanvraag",
            start_timestamp=0,
            end_timestamp=0,
            resource="User_1",
            attributes={},
        ),
        Event(
            id=3680006,
            activity="A_ACCEPTED",
            start_timestamp=0,
            end_timestamp=0,
            resource="User_1",
            attributes={},
        )
    ]
