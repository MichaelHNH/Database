from flask import Flask, render_template,jsonify
from Statistik_sqlite import get_occupancy_data
app = Flask(__name__)

#rumnumre
rooms = [
    {"id": 1, "name": "D316a", "is_free": True},
    {"id": 2, "name": "D315", "is_free": True},
    {"id": 3, "name": "D223", "is_free": True},
    {"id": 4, "name": "D222", "is_free": True},
    {"id": 5, "name": "D224", "is_free": True},
    {"id": 6, "name": "D163", "is_free": True},
    {"id": 7, "name": "D164", "is_free": True},
    {"id": 8, "name": "D166", "is_free": True},
]
@app.route('/')
def index():
    return render_template("map1.html", rooms=rooms)

@app.route('/map1')
def map1():
    # Opdater rum-status fra database.txt
    for r in rooms:
        r["is_free"] = room_status(r["id"])
    return render_template("map1.html", rooms=rooms)


@app.route('/map2')
def map2():
    for r in rooms:
        r["is_free"] = room_status(r["id"])
    return render_template("map2.html", rooms=rooms)

@app.route('/map3')
def map3():
    for r in rooms:
        r["is_free"] = room_status(r["id"])
    return render_template("map3.html", rooms=rooms)

#Viser rum baseret på id
@app.route('/room/<int:room_id>')
def rummap(room_id):
    room = next((r for r in rooms if r["id"] == room_id), None)
    if not room:
        return "Dette er ikke et rum"
    return render_template("rummap.html", room=room)

def room_status(room_id):
    is_free = True #gør standard til = ledigt
    try:
        with open("database.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            # læser fra bunden, da txt filen nok opdatere, og så finder status på rummene #Højst sandsynligt ændres data base til sqlite
            for line in reversed(lines):
                if f"room={room_id}" in line:
                    if "occupied" in line:
                        is_free = False
                    elif "free" in line:
                        is_free = True
                    break
    except FileNotFoundError:
        pass
    return is_free

@app.route('/data')
def data():
    """Leverer data til grafen i JSON-format."""
    occupancy_data = get_occupancy_data()
    return jsonify(occupancy_data)

if __name__ == '__main__':
    app.run(debug=True)
