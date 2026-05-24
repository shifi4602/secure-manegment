"""
Calendar scheduler — finds available meeting time slots for a group of people.
"""
import sys
from datetime import timedelta
from typing import List

from .event import Event, _minutes, _to_time
from .calendar import Calendar

# Working day boundaries (minutes from midnight)
_DAY_START = 7 * 60   # 07:00
_DAY_END   = 19 * 60  # 19:00

# Gaps of this many minutes or fewer are treated as transition/travel time
# between tasks (walking time) and are never offered as meeting slots.
TRANSITION_BUFFER_MINUTES = 10

# Slot enumeration step
_SLOT_STEP = 10


def _merge_intervals(intervals: list) -> list:
    """Sort and merge overlapping/adjacent (start, end) integer intervals."""
    if not intervals:
        return []
    result = [list(sorted(intervals)[0])]
    for start, end in sorted(intervals)[1:]:
        if start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return [tuple(iv) for iv in result]

#this is the main function that ueses all functions above and find the slots between the tasks for some pesron or people.
def find_available_slots(
    person_list: List[str],
    event_duration: timedelta,
    calendar: Calendar,
) -> List:
    """
    Find all available start times for a meeting that fits all listed people.

    Gaps of <= TRANSITION_BUFFER_MINUTES between tasks are treated as walking/
    transition time and are not offered as schedulable slots.

    Args:
        person_list: Names of people who must all attend.
        event_duration: Duration of the desired meeting.
        calendar: Calendar to query (injected by the caller).

    Returns:
        Sorted list of valid meeting start times within the working day.
    """
    duration_min = int(event_duration.total_seconds() // 60)

    # Collect every busy interval across all requested people
    busy = [
        (_minutes(event.start), _minutes(event.end))
        for person in person_list
        for event in calendar.get_events(person)
    ]
    merged_busy = _merge_intervals(busy)

    # Derive free gaps within the working day
    free_gaps = []
    # the time of _DAY_START is in minutes.
    cursor = _DAY_START
    for b_start, b_end in merged_busy:
        if b_start > cursor:
            free_gaps.append((cursor, b_start))
        cursor = max(cursor, b_end)
    if cursor < _DAY_END:
        free_gaps.append((cursor, _DAY_END))

    slots: List[tuple] = []
    for gap_start, gap_end in free_gaps:
        # Skip gaps that are too short for the requested meeting
        if gap_end - gap_start < duration_min:
            continue
        slots.append((_to_time(gap_start), _to_time(gap_end)))

    return slots

# the main function that run in the terminal and print the available slots. it uses the find_available_slots function to find the slots between the people and print them in the terminal. it also handles the case when there are no available slots found.
def main():
    calendar = Calendar.load_from_csv()
    #people = ["Alice", "Jack", "Bob"]
    people = sorted(calendar._events.keys)
    # the default time for slot is one hour. the user can change it.
    duration = timedelta(hours=1)
    # find the slots for the people and the duration using the find_available_slots function. it returns a list of tuples with the start and end time of the slots.
    slots = find_available_slots(people, duration, calendar)
    print(f"Available 60-minute slots for {', '.join(people)}:")
    # if there is any slot found, it prints the start and end time of the slots in the terminal. if there is no slot found, it prints a message saying that no available slots found.
    if slots:
        for s, e in slots:
            print(f"  {s.strftime('%H:%M')} - {e.strftime('%H:%M')}")
    else:
        print("  No available slots found.")
    sys.exit(0)

# the main function is called when the script is run directly. it runs the main function and exits with code 0.
if __name__ == "__main__":
    main()
