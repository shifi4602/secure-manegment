"""
Event data class and time-conversion helpers.
"""
from dataclasses import dataclass
from datetime import time

# helper function to convert all time to minutes from midnight. 
# this is used to simplify the calculations when finding available slots.
# it takes a time object and returns the total number of minutes from midnight.
def _minutes(t: time) -> int:
    """Convert a time object to minutes from midnight."""
    return t.hour * 60 + t.minute

# helper function to convert minutes from midnight back to a time object. 
# this is used to convert the available slots back to time objects before returning them.
def _to_time(minutes: int) -> time:
    """Convert minutes from midnight back to a time object."""
    return time(minutes // 60, minutes % 60)

# helper function to parse a time string in the format 'HH:MM' and convert it to a time object.
def _parse_time(s: str) -> time:
    """Parse 'HH:MM' string into a time object."""
    h, m = s.strip().split(":")
    return time(int(h), int(m))

# Event data class that represents a calendar event. It has fields for the person, subject, start time, and end time. 
# The __post_init__ method checks that the start time is before the end time and raises a ValueError if it is not.
@dataclass
class Event:
    person: str
    subject: str
    start: time
    end: time

    # there is a test that checks that the start time is before the end time, so this method is used to enforce that constraint. 
    # if the start time is not before the end time, it raises a ValueError with a message that includes the event subject, person, and the invalid start and end times.
    # the test is on this function.
    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError(
                f"Event '{self.subject}' for {self.person}: "
                f"start ({self.start}) must be before end ({self.end})"
            )
