import sqlite3


def get_occupancy_data():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

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
    conn.close()

    labels = [row['hour'] for row in rows]
    data = [row['occupied_percentage'] for row in rows]

    return {'labels': labels, 'data': data}

