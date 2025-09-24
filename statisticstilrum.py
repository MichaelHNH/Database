import re
from datetime import datetime
from collections import defaultdict

LOG_FILE = "database.txt"


def parse_log_line(line):
    """
    Parses a line from database.txt and extracts room stats.
    """
    pattern = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| room=(?P<room>\d+) \| (?P<status>occupied|free)(?: \| distance=(?P<distance>\d+) \| energy=(?P<energy>\d+))?"
    )
    m = pattern.match(line.strip())
    if not m:
        return None

    data = m.groupdict()
    data["room"] = int(data["room"])
    data["distance"] = int(data["distance"]) if data["distance"] else None
    data["energy"] = int(data["energy"]) if data["energy"] else None
    data["timestamp"] = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
    return data


def get_room_stats(room_id, logfile=LOG_FILE):
    """
    Reads database.txt and generates statistics for a given room.
    Includes daily occupied/free durations in minutes + totals.
    Also calculates how long the room has been free in a row.
    """
    total = 0
    occupied_count = 0
    free_count = 0
    distances = []
    energies = []
    entries = []

    try:
        with open(logfile, "r", encoding="utf-8") as f:
            for line in f:
                entry = parse_log_line(line)
                if not entry:
                    continue
                if entry["room"] != room_id:
                    continue
                entries.append(entry)
                total += 1
                if entry["status"] == "occupied":
                    occupied_count += 1
                    if entry["distance"] is not None:
                        distances.append(entry["distance"])
                    if entry["energy"] is not None:
                        energies.append(entry["energy"])
                elif entry["status"] == "free":
                    free_count += 1
    except FileNotFoundError:
        return {"error": "database.txt not found"}

    # --- Calculate daily durations ---
    daily_stats = defaultdict(lambda: {"occupied_minutes": 0, "free_minutes": 0})
    total_occupied_minutes = 0
    total_free_minutes = 0

    for i in range(len(entries) - 1):
        curr = entries[i]
        nxt = entries[i + 1]

        diff = (nxt["timestamp"] - curr["timestamp"]).total_seconds() / 60.0
        day = curr["timestamp"].date()

        if curr["status"] == "occupied":
            daily_stats[day]["occupied_minutes"] += diff
            total_occupied_minutes += diff
        elif curr["status"] == "free":
            daily_stats[day]["free_minutes"] += diff
            total_free_minutes += diff

    # --- Calculate current free streak ---
    current_free_minutes = 0
    if entries:
        last_entry = entries[-1]
        if last_entry["status"] == "free":
            # look backwards until last occupied
            free_start = last_entry["timestamp"]
            for prev in reversed(entries[:-1]):
                if prev["status"] == "occupied":
                    break
                free_start = prev["timestamp"]
            current_free_minutes = (datetime.now() - free_start).total_seconds() / 60.0

    stats = {
        "room_id": room_id,
        "total gange målt": total,
        "antal optaget målinger": occupied_count,
        "antal fri målinger": free_count,
        "procentdel optaget": (occupied_count / total * 100) if total else 0,
        "Daglig statistik": dict(daily_stats),
        "antal minutter rummet har været optaget i alt": total_occupied_minutes,
        "antal minutter rummet har været fri i alt": total_free_minutes,
        "Rummet har været fri i...": current_free_minutes,
    }
    return stats


if __name__ == "__main__":
    room_id = 1
    stats = get_room_stats(room_id)
    print(f"Stats for room {room_id}:")
    for k, v in stats.items():
        if k != "daily_stats":
            if isinstance(v, float):
                print(f" - {k}: {v:.1f}")
            else:
                print(f" - {k}: {v}")
    print("Daglig statistik for rum X(erstat med rum nummer):")
    for day, d in stats["daily_stats"].items():
        print(f" {day}: occupied={d['occupied_minutes']:.1f} min, free={d['free_minutes']:.1f} min")
