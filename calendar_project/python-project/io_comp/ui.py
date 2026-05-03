"""
Web UI for the Calendar Scheduler.
Run with: python -m io_comp.ui
"""
from pathlib import Path
from datetime import timedelta

from flask import Flask, render_template, request, jsonify

from .calendar import Calendar
from .app import find_available_slots

_TEMPLATES = Path(__file__).parent / "templates"

app = Flask(__name__, template_folder=str(_TEMPLATES))
_calendar = Calendar.load_from_csv()


@app.route("/")
def index():
    people = sorted(_calendar._events.keys())
    return render_template("index.html", people=people)


@app.route("/find-slots", methods=["POST"])
def api_find_slots():
    data = request.get_json(force=True) or {}

    person_list = data.get("people", [])
    if not isinstance(person_list, list):
        return jsonify({"error": "Invalid people list"}), 400

    # Validate people names against known calendar entries
    known = set(_calendar._events.keys())
    person_list = [p for p in person_list if isinstance(p, str) and p in known]

    try:
        hours = max(0, min(23, int(data.get("hours", 0))))
        minutes = max(0, min(59, int(data.get("minutes", 0))))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid duration"}), 400

    if hours == 0 and minutes == 0:
        return jsonify({"error": "Duration must be greater than 0"}), 400

    duration = timedelta(hours=hours, minutes=minutes)
    slots = find_available_slots(person_list, duration, _calendar)
    return jsonify({"slots": [{"start": s.strftime("%H:%M"), "end": e.strftime("%H:%M")} for s, e in slots]})


@app.route("/person-events")
def api_person_events():
    person = request.args.get("person", "").strip()
    known = set(_calendar._events.keys())
    if person not in known:
        return jsonify({"error": "Unknown person"}), 400
    events = _calendar.get_events(person)
    return jsonify({
        "events": [
            {
                "subject": e.subject,
                "start": e.start.strftime("%H:%M"),
                "end": e.end.strftime("%H:%M"),
            }
            for e in events
        ]
    })


def main():
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
