from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import sqlite3
import os
from database import get_occupancy_data
from datetime import datetime, timedelta




app = Flask(__name__)
app.secret_key = "nøglehemmelig"#Gør at den "husker" brugeren er logget ind

BASE_DIR = os.path.dirname(os.path.abspath(__file__))#De to databaser (TIL PA)
DB_ARDUINO = os.path.join(BASE_DIR, "database.db")   # til LEDIGHED og CO2DATA
DB_BOOKINGS = os.path.join(BASE_DIR, "bdatabase.db") # til bookings

# pt hardcorded brugere
USERS = {
    "sara": "1234",
    "michael": "123",
    "lærer": "lærer123"
}


#rumnumre
Rrooms = [
    {"id": 1, "name": "D316a", "is_free": True},
    {"id": 2, "name": "D315", "is_free": True},
    {"id": 3, "name": "D223", "is_free": True},
    {"id": 4, "name": "D222", "is_free": True},
    {"id": 5, "name": "D224", "is_free": True},
    {"id": 6, "name": "D163", "is_free": True},
    {"id": 7, "name": "D164", "is_free": True},
    {"id": 8, "name": "D166", "is_free": True},
]


def broom():
    # Ændre ikke de globale rum#Laver en kopi af rumene, så de ikke ændres,
    rooms = [dict(r) for r in Rrooms]

    luk_book()#luk book hvis det ikke er nogen

    for r in rooms:
        arduino_status = room_status(r["id"])#Tjek hvad siger snesor
        booking_status = is_booked(r["id"])#er der en booking
        r["is_free"] = (arduino_status and not booking_status)
    return rooms
@app.route('/')
def index():
    rooms = broom()
    return render_template("map1.html", rooms=rooms)

@app.route('/map1')
def map1():
    rooms = broom()
    return render_template("map1.html", rooms=rooms)

@app.route('/map2')
def map2():
    rooms = broom()
    return render_template("map2.html", rooms=rooms)

@app.route('/map3')
def map3():
    rooms = broom()
    return render_template("map3.html", rooms=rooms)

def luk_book():
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")
    two_min_ago = (now - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M")
#Tjek nu, og fra to minutter siden
    # tjek alle aktive bookinger
    con = sqlite3.connect(DB_BOOKINGS)
    cur = con.cursor()
    cur.execute("""
        SELECT id, room_id FROM bookings
        WHERE datetime(start_time) <= datetime(?)
          AND datetime(end_time)   >= datetime(?)
          AND datetime(start_time) <= datetime(?)
    """, (now_str, now_str, two_min_ago))
    rows = cur.fetchall()
#Tjek alle bookninger der er igang
    # tjek for sensor
    updated = False
    for booking_id, room_id in rows:
        if room_status(room_id):
            cur.execute(
                "UPDATE bookings SET end_time = ? WHERE id = ?",
                (now_str, booking_id)
            )
            updated = True#tjekker ved sensor om rummet faktisk er free#hvis ja, så stop bookingen

    if updated:
        con.commit()
    con.close()


#Viser rum baseret på id
@app.route('/room/<int:room_id>')
def rummap(room_id):
    rooms = broom()
    room = next((r for r in rooms if r["id"] == room_id), None)
    if not room:
        return "Dette er ikke et rum"
    return render_template("rummap.html", room=room)

#Viser rummene, bruges når man trykker -> sendes til rummap (det er der hvor booking er)

def room_status(room_id: int) -> bool:#Tjek om sandt eller falsk i stedet
    con = sqlite3.connect(DB_ARDUINO)#Tag data fra databasend
    cur = con.cursor()
    cur.execute("""
        SELECT ledighed FROM LEDIGHED 
        WHERE room_id = ? 
        ORDER BY ts DESC LIMIT 1
    """, (room_id,))
    row = cur.fetchone()
    con.close()#Tjekker om rummene er ledige ud fra databasen ud fra sensorens data

    if row:
        return row[0] == "free"
    return True  # default = ledigt

def is_booked(room_id: int) -> bool:#tjek om rummene er booket
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
def login():#login og logout
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
    return count > 0#Tjekker om der allerede er en booking når en bruger prøver at book


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
        broom()

        flash(f"Booking oprettet af {user} for rum {room_id}!", "success")
        return redirect(url_for("rummap", room_id=room_id))

    return render_template("book.html", room_id=room_id)


@app.route('/bookings')
def show_bookings():#baretest
    con = sqlite3.connect(DB_BOOKINGS)
    cur = con.cursor()
    cur.execute("SELECT * FROM bookings")
    rows = cur.fetchall()
    con.close()
    return str(rows)


@app.route('/upload', methods=['POST'])
def upload():#Her sender den til PA
    data = request.json
    ts = data.get("ts")
    room_id = data.get("room_id")
    ledighed = data.get("ledighed")
    co2ppm = data.get("co2ppm")


    con = sqlite3.connect(DB_ARDUINO)
    cur = con.cursor()

#logger alt data, laver en tabel
    cur.execute("""
        CREATE TABLE IF NOT EXISTS SENSOR_LOG (
            nr_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            room_id INTEGER,
            ledighed TEXT,
            co2ppm INTEGER
        )
    """)

#Indsæt dataet
    cur.execute(
        "INSERT INTO SENSOR_LOG (ts, room_id, ledighed, co2ppm) VALUES (?, ?, ?, ?)",
        (ts, room_id, ledighed, co2ppm)#Logger alt i sensor log (skal nok ændres)
    )
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
