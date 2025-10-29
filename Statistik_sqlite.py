import sqlite3, os
try:
    from app import DB_ARDUINO
except ImportError:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_ARDUINO = os.path.join(BASE_DIR, "database.db")



def get_occupancy_data():
    con = sqlite3.connect(DB_ARDUINO)
    con.row_factory = sqlite3.Row
    cursor = con.cursor()

    query = """
    SELECT
        strftime('%Y-%m-%d %H:00', ts) as hour,
        (SUM(CASE WHEN ledighed = 'ocupied' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as occupied_percentage
    FROM
        LEDIGHED
    WHERE
        room_id = '1'
    GROUP BY
        hour
    ORDER BY
        hour;
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    con.close()

    labels = [row['hour'] for row in rows]
    data = [row['occupied_percentage'] for row in rows]

    return {'labels': labels, 'data': data}