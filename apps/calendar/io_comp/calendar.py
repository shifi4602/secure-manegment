"""
Calendar data class — loads and stores events per person.
"""
import csv
from pathlib import Path

# use the event class and time parsing function.
from .event import Event, _parse_time

# the path of the csv file that contain the calendar data.
_DEFAULT_CSV = Path(__file__).parent.parent / "resources" / "calendar.csv"


class Calendar:
    """Holds a collection of events keyed by person name."""

    # ctor that initializes the calendar with an empty dictionary to hold events.
    def __init__(self) -> None:
        self._events: dict = {}  # person -> list[Event]

    # helper function to read the csv file and create Event objects for each row in the csv file.
    # then it add the event to the calendar dictionary under the corresponding person key.
    # it returns a Calendar instance with the loaded events.
    @classmethod
    def load_from_csv(cls, path: Path = _DEFAULT_CSV) -> "Calendar":
        """Load calendar events from a CSV file (person, subject, HH:MM, HH:MM)."""
        cal = cls()
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) < 4:
                    continue
                event = Event(
                    person=row[0].strip(),
                    subject=row[1].strip(),
                    start=_parse_time(row[2]),
                    end=_parse_time(row[3]),
                )
                cal._events.setdefault(event.person, []).append(event)
        return cal

    # method to get the events for a specific person. it looks up the person in the calendar dictionary and returns a sorted list of events for that person. if the person is not found, it returns an empty list.
    def get_events(self, person: str) -> list:
        """Return events for a person sorted by start time."""
        return sorted(self._events.get(person, []), key=lambda e: e.start)
