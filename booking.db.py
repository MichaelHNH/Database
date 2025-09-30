import sqlite3

con = sqlite3.connect("bdatabase.db")
cur = con.cursor()

#Lav tabel
cur.execute("""
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL)
""")
#Specifikt ID, Rum id, User navn, start og slut tid, og test om rum id findes
cur.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY,
    room_id INTEGER,
    user TEXT,
    start_time TEXT,
    end_time TEXT, 
    FOREIGN KEY (room_id) REFERENCES rooms (id) 
)
""")

rooms = [
    (1, "D316a"),
    (2, "D315"),
    (3, "D223"),
    (4, "D222"),
    (5, "D224"),
    (6, "D163"),
    (7, "D164"),
    (8, "D166"),
]

cur.executemany("INSERT OR IGNORE INTO rooms (id, name) VALUES (?, ?)", rooms)


def get_bookings():
    con = sqlite3.connect("bdatabase.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM bookings")
    data = cur.fetchall()
    con.close()
    return data

def add_booking(room_id, user, start_time, end_time):
    con = sqlite3.connect("bdatabase.db")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO bookings (room_id, user, start_time, end_time)
        VALUES (?, ?, ?, ?)
    """, (room_id, user, start_time, end_time))
    con.commit()
    con.close()


con.commit()
con.close()

