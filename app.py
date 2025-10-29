from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import sqlite3
import os
from database import get_occupancy_data
from datetime import datetime




app = Flask(__name__)
app.secret_key = "nøglehemmelig"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_ARDUINO = os.path.join(BASE_DIR, "database.db")   # til LEDIGHED og CO2DATA
DB_BOOKINGS = os.path.join(BASE_DIR, "bdatabase.db") # til bookings

# pt hardcorded brugere
USERS = {
    "sara": "1234",
    "michael": "123",
    "lærer": "lærer123"
}


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
    opdater_status()
    return render_template("map1.html", rooms=rooms)

@app.route('/map2')
def map2():
    opdater_status()
    return render_template("map2.html", rooms=rooms)

@app.route('/map3')
def map3():
    opdater_status()
    return render_template("map3.html", rooms=rooms)

#Viser rum baseret på id
@app.route('/room/<int:room_id>')
def rummap(room_id):
    room = next((r for r in rooms if r["id"] == room_id), None)
    if not room:
        return "Dette er ikke et rum"
    return render_template("rummap.html", room=room)

def opdater_status():
    #Opdaterer status for rummene
    for r in rooms:
        arduino_status = room_status(r["id"])
        booking_status = is_booked(r["id"])
        r["is_free"] = (arduino_status and not booking_status)


def room_status(room_id: int) -> bool:#Tjek om sandt eller falsk i stedet
    con = sqlite3.connect(DB_ARDUINO)#Tag data fra databasend
    cur = con.cursor()
    cur.execute("""
        SELECT ledighed FROM LEDIGHED 
        WHERE room_id = ? 
        ORDER BY ts DESC LIMIT 1
    """, (room_id,))
    row = cur.fetchone()
    con.close()

    if row:
        return row[0] == "free"
    return True  # default = ledigt

def is_booked(room_id: int) -> bool:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    con = sqlite3.connect(DB_BOOKINGS)
    cur = con.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE room_id = ?
        AND datetime(start_time) <= datetime(?)
        AND datetime(end_time) >= datetime(?)
    """, (room_id, now, now))
    count = cur.fetchone()[0]
    con.close()

    return count > 0


@app.route('/data')
def data():
    """Leverer data til grafen i JSON-format."""
    occupancy_data = get_occupancy_data()
    return jsonify(occupancy_data)

@app.route('/login', methods=["GET", "POST"])
def login():
    next = request.form.get("next") or request.args.get("next")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in USERS and USERS[username] == password:
            session["user"] = username
            flash("Hej, " + username, "success")
            return redirect(next or url_for("index"))
        else:
            flash("Noget er vidst skrevet forkert, hmm.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop("user", None)
    flash("Du er nu logget ud", "info")
    return redirect(url_for("index"))

def bookingkonflikt(room_id: int, start_time: str, end_time: str, current_user: str) -> bool:
    con = sqlite3.connect(DB_BOOKINGS)#returnerer true elelr false, tjekker om en user har booket lokalet
    cur = con.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE room_id = ?
          AND datetime(start_time) < datetime(?)
          AND datetime(end_time)   > datetime(?)
          AND user <> ?
    """, (room_id, end_time, start_time, current_user))
    count = cur.fetchone()[0]
    con.close()
    return count > 0


@app.route('/book/<int:room_id>', methods=["GET", "POST"])
def book(room_id):
    if "user" not in session:
        target = url_for("book", room_id=room_id)
        if request.method == "POST":
            flash("Du skal logge ind for at kunne booke et rum!", "error")
        return redirect(url_for("login", next=target))

    user = session["user"]

    if request.method == "POST":
        start = datetime.strptime(request.form["start_time"], "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M")
        end   = datetime.strptime(request.form["end_time"],   "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M")

        if end <= start:
            flash("Sluttidspunktet skal være efter starttidspunktet.", "error")
            return redirect(url_for("book", room_id=room_id))

        if bookingkonflikt(room_id, start, end, user):
            flash("Dette rum er allerede booket på dette tidspunkt", "error")
            return redirect(url_for("book", room_id=room_id))

        con = sqlite3.connect(DB_BOOKINGS)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO bookings (room_id, user, start_time, end_time) VALUES (?, ?, ?, ?)",
            (room_id, user, start, end)
        )
        con.commit()
        con.close()
        opdater_status()

        flash(f"Booking oprettet af {user} for rum {room_id}!", "success")
        return redirect(url_for("rummap", room_id=room_id))

    return render_template("book.html", room_id=room_id)


@app.route('/bookings')
def show_bookings():
    con = sqlite3.connect(DB_BOOKINGS)
    cur = con.cursor()
    cur.execute("SELECT * FROM bookings")
    rows = cur.fetchall()
    con.close()
    return str(rows)


@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    ts = data.get("ts")
    room_id = data.get("room_id")
    ledighed = data.get("ledighed")
    co2ppm = data.get("co2ppm")

    con = sqlite3.connect(DB_ARDUINO)
    cur = con.cursor()

    if ledighed:
        cur.execute(
            "INSERT INTO LEDIGHED (ts, room_id, ledighed) VALUES (?, ?, ?)",
            (ts, room_id, ledighed)
        )

    if co2ppm is not None:
        cur.execute(
            "INSERT INTO CO2DATA (ts, room_id, co2ppm) VALUES (?, ?, ?)",
            (ts, room_id, co2ppm)
        )

    con.commit()
    con.close()

    return {"status": "ok"}
@app.route('/db')
def show_db_data():
    con = sqlite3.connect(DB_ARDUINO)
    cur = con.cursor()
    cur.execute("SELECT * FROM LEDIGHED")
    rows = cur.fetchall()
    con.close()
    return str(rows)


if __name__ == '__main__':
    app.run(debug=True)
