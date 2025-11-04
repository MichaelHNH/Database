from server import sensor_id_list
sensors= [1,2,3]

cur.execute("""
CREATE TABLE IF NOT EXISTS Sensors (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL)
""")

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
