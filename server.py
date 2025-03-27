import random
import string
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = "wubba lubba dub dub"

socketio = SocketIO(app)
users_in_room = {}
rooms_sid = {}
names_sid = {}

def generate_display_name():
    return "User-" + "".join(random.choices(string.ascii_letters + string.digits, k=6))

@app.route("/", methods=["GET"])
def join():
    display_name = request.args.get('display_name') or generate_display_name()
    mute_audio = request.args.get('mute_audio', 0)
    mute_video = request.args.get('mute_video', 0)
    room_id = request.args.get('room_id', "1")

    session[room_id] = {
        "name": display_name,
        "mute_audio": mute_audio,
        "mute_video": mute_video
    }
    return render_template("join.html", room_id=room_id, display_name=display_name,
                           mute_audio=mute_audio, mute_video=mute_video)

@socketio.on("connect")
def on_connect():
    pass

@socketio.on("join-room")
def on_join_room(data):
    sid = request.sid
    room_id = str(data.get("room_id", "1"))

    if room_id in session:
        display_name = session[room_id].get("name", generate_display_name())

        if room_id not in users_in_room:
            users_in_room[room_id] = []

        join_room(room_id)
        rooms_sid[sid] = room_id
        names_sid[sid] = display_name

        print("[{}] New member joined: {}<{}>".format(room_id, display_name, sid))
        emit("user-connect", {"sid": sid, "name": display_name}, broadcast=True, include_self=False, room=room_id)
        users_in_room[room_id].append(sid)

        usrlist = {u_id: names_sid[u_id] for u_id in users_in_room[room_id]}
        emit("user-list", {"list": usrlist, "my_id": sid})

        print("\nUsers in room:", users_in_room, "\n")
        return

    print("Invalid room ID or missing session data")

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    if sid in rooms_sid:
        room_id = rooms_sid[sid]
        display_name = names_sid.get(sid)

        if display_name:
            print("[{}] Member left: {}<{}>".format(room_id, display_name, sid))
            emit("user-disconnect", {"sid": sid}, broadcast=True, include_self=False, room=room_id)

            users_in_room[room_id].remove(sid)
            if not users_in_room[room_id]:
                users_in_room.pop(room_id)

            rooms_sid.pop(sid)
            names_sid.pop(sid)

            print("\nUsers in room:", users_in_room, "\n")
            return

    print("Socket not registered in any room")

@socketio.on("data")
def on_data(data):
    sender_sid = data.get('sender_id')
    target_sid = data.get('target_id')
    if sender_sid != request.sid:
        print("[Error] request.sid and sender_id don't match!!!")

    message_type = data.get("type")
    if message_type != "new-ice-candidate":
        print('{} message from {} to {}'.format(message_type, sender_sid, target_sid))

    socketio.emit('data', data, room=target_sid)

if __name__ == "__main__":
    socketio.run(app, port=6001, host='0.0.0.0')
