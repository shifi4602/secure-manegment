"""
Unit tests for Comp calendar scheduler
"""
from datetime import time, timedelta

import pytest

from io_comp.event import Event
from io_comp.calendar import Calendar
from io_comp.app import find_available_slots

# helper function to create a Calendar instance from a list of event tuples (person, subject, start_str, end_str). This is used in the tests to set up specific calendar scenarios without needing to read from a CSV file.
# it a unit test so it not reading from the csv file and using fake data to test the function.
# this function help to put the data in the calendar and then test the function will use it like in the real function it test.
def _make_calendar(rows):
    """Build a Calendar from (person, subject, 'HH:MM', 'HH:MM') tuples."""
    cal = Calendar()
    for person, subject, start_str, end_str in rows:
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        event = Event(person=person, subject=subject, start=time(sh, sm), end=time(eh, em))
        cal._events.setdefault(person, []).append(event)
    return cal


def test_alice_jack_60min():
    """
    Alice+Jack combined busy merges to: 08:00-09:40, 13:00-14:00, 16:00-17:00.
    Free gaps (all >10 min): 07:00-08:00, 09:40-13:00, 14:00-16:00, 17:00-19:00.
    """
    cal = _make_calendar([
        ("Alice", "Morning meeting",  "08:00", "09:30"),
        ("Alice", "Lunch with Jack",  "13:00", "14:00"),
        ("Alice", "Yoga",             "16:00", "17:00"),
        ("Jack",  "Morning meeting",  "08:00", "08:50"),
        ("Jack",  "Sales call",       "09:00", "09:40"),
        ("Jack",  "Lunch with Alice", "13:00", "14:00"),
        ("Jack",  "Yoga",             "16:00", "17:00"),
    ])
    slots = find_available_slots(["Alice", "Jack"], timedelta(hours=1), cal)

    # 07:00-08:00 gap (60 min): only 07:00 fits (07:00+60=08:00)
    assert time(7, 0)  in slots
    assert time(7, 10) not in slots     # 07:10+60=08:10 > 08:00

    # 09:40-13:00 gap (200 min): 09:40 … 12:00
    assert time(9, 40)  in slots
    assert time(12, 0)  in slots        # 12:00+60=13:00 — fits exactly
    assert time(12, 10) not in slots    # 12:10+60=13:10 > 13:00

    # 14:00-16:00 gap (120 min): 14:00 … 15:00
    assert time(14, 0)  in slots
    assert time(15, 0)  in slots        # 15:00+60=16:00 — fits exactly
    assert time(15, 10) not in slots    # 15:10+60=16:10 > 16:00

    # 17:00-19:00 gap (120 min): 17:00 … 18:00
    assert time(17, 0)  in slots
    assert time(18, 0)  in slots        # 18:00+60=19:00 — fits exactly
    assert time(18, 10) not in slots    # 18:10+60=19:10 > 19:00


def test_single_person_bob_30min():
    """
    Bob's busy merges to: 08:00-09:40, 10:00-11:30, 13:00-15:00, 16:00-17:00.
    Free gaps: 07:00-08:00 (60 min), 09:40-10:00 (20 min, > buffer but too short
    for a 30-min meeting), 11:30-13:00 (90 min), 15:00-16:00 (60 min),
    17:00-19:00 (120 min).
    """
    cal = _make_calendar([
        ("Bob", "Morning meeting",   "08:00", "09:30"),
        ("Bob", "Morning meeting 2", "09:30", "09:40"),  # merges with previous
        ("Bob", "Q3 review",         "10:00", "11:30"),
        ("Bob", "Lunch and siesta",  "13:00", "15:00"),
        ("Bob", "Yoga",              "16:00", "17:00"),
    ])
    slots = find_available_slots(["Bob"], timedelta(minutes=30), cal)

    # 07:00-08:00 gap: slots 07:00 … 07:30
    assert time(7, 0)  in slots
    assert time(7, 30) in slots         # 07:30+30=08:00 — fits exactly
    assert time(7, 40) not in slots     # 07:40+30=08:10 > 08:00

    # 09:40-10:00 gap (20 min > buffer): 09:40+30=10:10 > 10:00 — no 30-min slot fits
    assert time(9, 40) not in slots

    # 11:30-13:00 gap: slots 11:30 … 12:30
    assert time(11, 30) in slots
    assert time(12, 30) in slots        # 12:30+30=13:00 — fits exactly
    assert time(12, 40) not in slots    # 12:40+30=13:10 > 13:00

    # 15:00-16:00 and 17:00-19:00 gaps
    assert time(15, 0)  in slots
    assert time(17, 0)  in slots
    assert time(18, 30) in slots        # 18:30+30=19:00 — fits exactly
    assert time(18, 40) not in slots    # 18:40+30=19:10 > 19:00


def test_duration_too_long_returns_empty():
    """A meeting longer than every free gap produces no slots."""
    cal = _make_calendar([
        ("Alice", "Morning meeting", "08:00", "09:30"),
        ("Alice", "Lunch",           "13:00", "14:00"),
        ("Alice", "Yoga",            "16:00", "17:00"),
    ])
    # Longest free gap is 09:30-13:00 = 210 min; 4 h = 240 min won't fit anywhere
    slots = find_available_slots(["Alice"], timedelta(hours=4), cal)
    assert slots == []


def test_fully_booked_no_slots():
    """
    Carol's schedule covers the entire workday 07:00-19:00 with no gaps at all.
    No slot of any size should be returned.
    """
    cal = _make_calendar([
        ("Carol", "Early meeting",   "07:00", "09:00"),
        ("Carol", "Project sync",    "09:00", "12:00"),
        ("Carol", "Lunch meeting",   "12:00", "14:00"),
        ("Carol", "Afternoon block", "14:00", "17:00"),
        ("Carol", "Late call",       "17:00", "19:00"),
    ])
    slots = find_available_slots(["Carol"], timedelta(minutes=30), cal)
    assert slots == []


def test_two_people_combined_fully_booked_no_slots():
    """
    Dave is busy 07:00-13:00 and Eve is busy 13:00-19:00.
    Their combined busy time covers the entire day, leaving no free slot for both.
    """
    cal = _make_calendar([
        ("Dave", "Morning block", "07:00", "13:00"),
        ("Eve",  "Afternoon",     "13:00", "19:00"),
    ])
    slots = find_available_slots(["Dave", "Eve"], timedelta(minutes=15), cal)
    assert slots == []


def test_event_start_not_before_end_raises():
    """
    An Event whose start time is equal to or later than its end time is invalid.
    Creating such an Event should raise a ValueError.

    Valid event:   start=09:00, end=10:00  (start < end) — OK
    Invalid event: start=10:00, end=09:00  (start > end) — should raise
    Invalid event: start=09:00, end=09:00  (start == end) — should raise
    """
    # A valid event should not raise
    valid_event = Event(person="Frank", subject="Valid", start=time(9, 0), end=time(10, 0))
    assert valid_event.start < valid_event.end

    # start is after end — must raise ValueError
    with pytest.raises(ValueError):
        Event(person="Frank", subject="Reversed", start=time(10, 0), end=time(9, 0))

    # start equals end (zero-duration) — must raise ValueError
    with pytest.raises(ValueError):
        Event(person="Frank", subject="Zero duration", start=time(9, 0), end=time(9, 0))
