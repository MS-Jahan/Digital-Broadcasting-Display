import os
import sqlite3
from flask import Flask, render_template, session, copy_current_request_context, send_from_directory, request, redirect, url_for, redirect, url_for
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from eventlet import wsgi
import eventlet
import traceback
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

app.config['SECRET_KEY'] = 'secret!'
app.config['VIDEO_FOLDER'] = 'videos'
socket_ = SocketIO(app)
thread = None
thread_lock = Lock()

# Create the SQLite database connection
conn = sqlite3.connect('database.sqlite')
conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key support

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    cursor = conn.execute('SELECT * FROM user WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return User(*row)
    return None


class Video:
    def __init__(self, id, filename, status):
        self.id = id
        self.filename = filename
        self.status = status


class UnlistedVideo:
    def __init__(self, id, filename, status):
        self.id = id
        self.filename = filename
        self.status = status


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def startup_tasks():
    if not os.path.exists(app.config['VIDEO_FOLDER']):
        os.mkdir(app.config['VIDEO_FOLDER'])

    # Create the videos table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS video (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    # Populate the videos table
    with conn:
        cursor = conn.execute('SELECT filename FROM video')
        existing_videos = set(row[0] for row in cursor.fetchall())

        videos = os.listdir(app.config['VIDEO_FOLDER'])
        for video in videos:
            if video not in existing_videos:
                print("[+] Adding video: " + video)
                conn.execute('INSERT INTO video (filename, status) VALUES (?, ?)', (video, 'listed'))


@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/admin')
# @login_required
def admin():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('admin/index.html')


@app.route('/all_videos')
@login_required
def all_videos():
    cursor = conn.execute('SELECT * FROM video')
    videos = [Video(*row) for row in cursor.fetchall()]

    videos_arr = []
    unlisted_videos_arr = []
    for video in videos:
        if video.status == 'unlisted':
            unlisted_videos_arr.append(video.filename)
        else:
            videos_arr.append(video.filename)

    return {"videos": videos_arr, "unlisted_videos": unlisted_videos_arr}


@app.route('/videos/<path:filename>')
@login_required
def videos(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)


@app.route('/playlist_index_swap', methods=['GET'])
@login_required
def pi_swap():
    one = int(request.args.get('one'))
    another = int(request.args.get('another'))

    with conn:
        cursor = conn.execute('SELECT * FROM video ORDER BY id LIMIT 2 OFFSET ?', (one,))
        videos = [Video(*row) for row in cursor.fetchall()]

        if len(videos) != 2:
            return {"message": "Invalid indices"}

        videos[0].id, videos[1].id = videos[1].id, videos[0].id

    return {"message": "success"}


@app.route('/make_video_unlisted', methods=['GET'])
@login_required
def make_video_unlisted():
    try:
        video_id = int(request.args.get('id'))

        with conn:
            cursor = conn.execute('SELECT * FROM video WHERE id = ?', (video_id,))
            row = cursor.fetchone()

            if row is None:
                return {"message": "Invalid video ID"}

            unlisted_video = UnlistedVideo(*row)
            conn.execute('DELETE FROM video WHERE id = ?', (video_id,))
            conn.execute('INSERT INTO unlisted_video (id, filename, status) VALUES (?, ?, ?)',
                         (unlisted_video.id, unlisted_video.filename, unlisted_video.status))

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400


@app.route('/make_video_listed', methods=['GET'])
@login_required
def make_video_listed():
    try:
        video_id = int(request.args.get('id'))

        with conn:
            cursor = conn.execute('SELECT * FROM unlisted_video WHERE id = ?', (video_id,))
            row = cursor.fetchone()

            if row is None:
                return {"message": "Invalid video ID"}

            video = Video(*row)
            conn.execute('DELETE FROM unlisted_video WHERE id = ?', (video_id,))
            conn.execute('INSERT INTO video (id, filename, status) VALUES (?, ?, ?)',
                         (video.id, video.filename, video.status))

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400


@app.route('/delete_video', methods=['GET'])
@login_required
def delete_video():
    try:
        video_id = int(request.args.get('id'))

        with conn:
            cursor = conn.execute('SELECT * FROM video WHERE id = ?', (video_id,))
            row = cursor.fetchone()

            if row is None:
                return {"message": "Invalid video ID"}

            video = Video(*row)
            video_path = os.path.join(app.config['VIDEO_FOLDER'], video.filename)
            os.remove(video_path)
            conn.execute('DELETE FROM video WHERE id = ?', (video_id,))

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400


@socket_.on('my_event', namespace='/test')
@login_required
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': message['data'], 'count': session['receive_count']})


@socket_.on('my_broadcast_event', namespace='/test')
@login_required
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': message['data'], 'count': session['receive_count']}, broadcast=True)


@socket_.on('disconnect_request', namespace='/test')
@login_required
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Disconnected!', 'count': session['receive_count']}, callback=can_disconnect)


@socket_.on('next_video', namespace='/video')
@login_required
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    current_video_index = message['current_video_index']

    try:
        with conn:
            cursor = conn.execute('SELECT * FROM video ORDER BY id')
            videos = [Video(*row) for row in cursor.fetchall()]

            if len(videos) == 0:
                raise Exception("No videos in the local store")

            current_video_index += 1
            if current_video_index >= len(videos):
                current_video_index = 0

            next_video = videos[current_video_index]
            emit('next_video', {'video_id': next_video.id, 'video_name': next_video.filename})
    except Exception as e:
        print(traceback.format_exc())


@socket_.on('connect', namespace='/video')
@login_required
def send_play_command():
    try:
        emit('play_video', {'data': 'play_video'})
    except Exception as e:
        raise e


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cursor = conn.execute('SELECT * FROM user WHERE username = ?', (username,))
        row = cursor.fetchone()

        if row is None or row[2] != password:
            return redirect(url_for('login'))

        user = User(*row)
        login_user(user)
        return redirect(url_for('admin'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    startup_tasks()
    # socket_.run(app, port=8082, debug=True)
    wsgi.server(eventlet.listen(('', 8082)), app)
