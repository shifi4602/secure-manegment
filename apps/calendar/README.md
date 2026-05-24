# Comp In-Office Coding Evaluation - Python

Welcome to the Python starter project for Comp's coding evaluation!

## Getting Started

### Prerequisites

You will need Python 3.8 or higher installed on your machine.

### Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Install the package in development mode:
```bash
pip install -e .
```

### Running the Application

To execute the app, you can run:
```bash
python -m io_comp.app
```

Or use the installed console script:
```bash
Comp-calendar
```

### Running Tests

To run the tests:
```bash
pytest
```

To run tests with verbose output:
```bash
pytest -v
```

## Project Structure

```
python-project/
├── io_Comp/              # Main application package
│   ├── __init__.py
│   └── app.py            # Application entry point
├── tests/                # Test directory
│   ├── __init__.py
│   └── test_app.py       # Unit tests
├── resources/            # Resources directory
│   └── calendar.csv      # Example calendar data
├── requirements.txt      # Python dependencies
├── setup.py             # Package configuration
└── README.md            # This file
```

## Your Task

Implement a calendar application that can find available time slots. See the main [README.md](../README.md) in the root directory for complete requirements.

### Method Signature

```python
from typing import List
from datetime import time, timedelta

def find_available_slots(person_list: List[str], event_duration: timedelta) -> List[time]:
    """
    Find all available time slots for a meeting with the given people and duration.

    Args:
        person_list: List of person names who should attend the meeting
        event_duration: Duration of the desired meeting

    Returns:
        List of start times when all persons are available
    """
    pass
```

## Tips

- The calendar data is available in `resources/calendar.csv`
- Python's `datetime` module provides useful classes like `time`, `datetime`, and `timedelta`
- Consider using classes to represent Calendar, Event, Person, etc.
- Follow PEP 8 style guidelines
- Write clean, modular, and well-documented code
- Don't forget to implement 2-3 meaningful tests!

Good luck!
