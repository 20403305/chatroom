import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, send, disconnect
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'files_display'
socketio = SocketIO(app)

users = {}
chatrooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/files')
def list_files():
    base_dir = request.args.get('dir', '')
    directory = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(base_dir))
    if os.path.exists(directory) and os.path.isdir(directory):
        files = os.listdir(directory)
        return jsonify({'files': files, 'current_dir': base_dir})
    else:
        return jsonify({'error': 'Directory not found'}), 404

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    target_dir = request.form.get('dir', '')
    directory = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(target_dir))

    if not os.path.exists(directory):
        os.makedirs(directory)

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(directory, filename))
    return jsonify({'success': 'File uploaded successfully'})

@socketio.on('join')
def on_join(data):
    username = data['username']
    new_room = data['room']
    sid = request.sid
    
    # Check if the username already exists in the room
    if new_room in chatrooms and username in chatrooms[new_room]:
        socketio.emit('error', {'message': "Username already exists in this room. Please choose another one."}, to=sid)
        return

    # Remove user from old room if exists
    old_room = users.get(sid, None)
    if old_room and old_room in chatrooms:
        if username in chatrooms[old_room]:
            chatrooms[old_room].remove(username)
            if not chatrooms[old_room]:
                del chatrooms[old_room]
            leave_room(old_room)
            send(f"---------{username} ({request.remote_addr}) has left the room.---------", room=old_room)

    # Add user to new room
    users[sid] = new_room
    if new_room not in chatrooms:
        chatrooms[new_room] = []
    chatrooms[new_room].append(username)
    join_room(new_room)
    send(f"---------{username} ({request.remote_addr}) has entered the room.---------", room=new_room)
    update_rooms()

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    sid = request.sid
    if room in chatrooms and username in chatrooms[room]:
        leave_room(room)
        chatrooms[room].remove(username)
        if not chatrooms[room]:
            del chatrooms[room]
        del users[sid]
        send(f"---------{username} ({request.remote_addr}) has left the room.---------", room=room)
        update_rooms()

@socketio.on('message')
def handle_message(data):
    room = data['room']
    send(f"{data['username']} ({request.remote_addr}): {data['message']}", room=room)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in users:
        username = None
        room = users[sid]
        if room in chatrooms:
            for user in chatrooms[room]:
                if request.sid == sid:
                    username = user
                    break
            if username:
                chatrooms[room].remove(username)
                send(f"---------{username} ({request.remote_addr}) has left the room.---------", room=room)
                if not chatrooms[room]:
                    del chatrooms[room]
                del users[sid]
                update_rooms()

def update_rooms():
    rooms_info = {room: len(users) for room, users in chatrooms.items()}
    socketio.emit('update_rooms', rooms_info)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    socketio.run(app, debug=True)
