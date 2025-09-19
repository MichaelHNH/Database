from flask import Flask, render_template

app = Flask(__name__)

#Ingen data, så bare hardcoded
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
#Viser rum baseret på id
@app.route('/room/<int:room_id>')
def rummap(room_id):
    room = next((r for r in rooms if r["id"] == room_id), None)
    if not room:
        return "Dette er ikke et rum"
    return render_template("rummap.html", room=room)

if __name__ == '__main__':
    app.run(debug=True)
