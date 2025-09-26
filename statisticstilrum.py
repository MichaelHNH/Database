import re
from datetime import datetime
from collections import defaultdict

LOG_FILE = "database.db.py"


def parse_log_line(line):
    pattern = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| room=(?P<room>\d+)"
        r" \| (?P<status>occupied|free)"
        r"(?: \| distance=(?P<distance>\d+))?"
        r"(?: \| energy=(?P<energy>\d+))?"
        r"(?: \| co2=(?P<co2>\d+))?"
        r"(?: \| temp=(?P<temp>-?\d+(?:\.\d+)?))?"
        r"(?: \| hum=(?P<hum>\d+(?:\.\d+)?))?"
    )
    m = pattern.match(line.strip())
    if not m:
        return None

    data = m.groupdict()
    data["room"] = int(data["room"])
    data["distance"] = int(data["distance"]) if data["distance"] else None
    data["energy"] = int(data["energy"]) if data["energy"] else None
    data["co2"] = int(data["co2"]) if data["co2"] else None
    data["temp"] = float(data["temp"]) if data["temp"] else None
    data["hum"] = float(data["hum"]) if data["hum"] else None
    data["timestamp"] = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
    return data


def get_room_stats(room_id, logfile=LOG_FILE):
    total = 0
    occupied_count = 0
    free_count = 0
    distances = []
    energies = []
    co2_values = []
    temps = []
    hums = []
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
                elif entry["status"] == "free":
                    free_count += 1

                if entry["distance"] is not None:
                    distances.append(entry["distance"])
                if entry["energy"] is not None:
                    energies.append(entry["energy"])
                if entry["co2"] is not None:
                    co2_values.append(entry["co2"])
                if entry["temp"] is not None:
                    temps.append(entry["temp"])
                if entry["hum"] is not None:
                    hums.append(entry["hum"])
    except FileNotFoundError:
        return {"error": "database.db.py not found"}

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
            free_start = last_entry["timestamp"]
            for prev in reversed(entries[:-1]):
                if prev["status"] == "occupied":
                    break
                free_start = prev["timestamp"]
            current_free_minutes = (datetime.now() - free_start).total_seconds() / 60.0

    # --- Prepare results ---
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

    # måler CO2, temperatur og luftfugtighedhvor at bestemme om der er blevet luftet ud
    if co2_values:
        stats["gennemsnitlig CO2"] = sum(co2_values) / len(co2_values)
        stats["maks CO2"] = max(co2_values)
        stats["min CO2"] = min(co2_values)
    if temps:
        stats["gennemsnitlig temperatur"] = sum(temps) / len(temps)
    if hums:
        stats["gennemsnitlig luftfugtighed"] = sum(hums) / len(hums)

    return stats


if __name__ == "__main__":
    room_id = 1
    stats = get_room_stats(room_id)
    print(f"Stats for room {room_id}:")
    for k, v in stats.items():
        if k != "Daglig statistik":
            if isinstance(v, float):
                print(f" - {k}: {v:.1f}")
            else:
                print(f" - {k}: {v}")
    print(f"Daglig statistik for rum {room_id}:")
    for day, d in stats["Daglig statistik"].items():
        print(f" {day}: occupied={d['occupied_minutes']:.1f} min, free={d['free_minutes']:.1f} min")
