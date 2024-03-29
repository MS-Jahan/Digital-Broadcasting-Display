import os
import sqlite3
from flask import Flask, render_template, session, copy_current_request_context, send_from_directory, request, redirect, url_for, redirect, url_for, session
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user, logout_user
from eventlet import wsgi
import eventlet
import traceback
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import timedelta

UPLOAD_FOLDER = 'videos'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

app = Flask(__name__)
CORS(app, supports_credentials=True)

socket_ = SocketIO(app)
thread = None
thread_lock = Lock()

CURRENTLY_PLAYING_VIDEO_NAME = None

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=1461)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

app.config['SECRET_KEY'] = 'secret!'
app.config['VIDEO_FOLDER'] = 'videos'

# Create the SQLite database connection
conn = sqlite3.connect('database.sqlite')
conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key support

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

class Subtitle:
    def __init__(self, content):
        self.content = content


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

    # Create the subtitle table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS subtitle (
            content TEXT NOT NULL
        )
    ''')


    subtitle_entry = Subtitle('')

    # Populate the videos table
    with conn:
        cursor = conn.execute('SELECT filename FROM video')
        existing_videos = set(row[0] for row in cursor.fetchall())

        videos = os.listdir(app.config['VIDEO_FOLDER'])

        # delete any non-existing videos
        for video in existing_videos:
            if video not in videos:
                print("[+] Deleting video: " + video)
                conn.execute('DELETE FROM video WHERE filename = ?', (video,))

        for video in videos:
            if video not in existing_videos:
                print("[+] Adding video: " + video)
                conn.execute('INSERT INTO video (filename, status) VALUES (?, ?)', (video, 'listed'))
        


@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login') + "?next=" + url_for('index'))
    return render_template('index.html')

@app.route('/admin')
# @login_required
def admin():
    if not current_user.is_authenticated:
        return redirect(url_for('login') + "?next=" + url_for('admin'))
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
            unlisted_videos_arr.append({video.id: video.filename})
        else:
            videos_arr.append({video.id: video.filename})

    return {"videos": videos_arr, "unlisted_videos": unlisted_videos_arr}


@app.route('/videos/<path:filename>')
@login_required
def videos(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)


@app.route('/subtitle', methods=['POST'])
@login_required
def update_subtitle():
    # get content from request json
    content = request.json['content']

    print(content)

    with conn:
        cursor = conn.execute('SELECT * FROM subtitle')
        row = cursor.fetchone()

        if row is None:
            # Insert new subtitle entry
            conn.execute('INSERT INTO subtitle (content) VALUES (?)', (content,))
        else:
            # Update existing subtitle entry
            conn.execute('UPDATE subtitle SET content = ?', (content,))

    # socket emit subtitle_updated
    socket_.emit('subtitle_updated', {'content': content}, namespace='/video')

    return {"message": "success"}


@app.route('/subtitle', methods=['GET'])
@login_required
def get_subtitle():
    with conn:
        cursor = conn.execute('SELECT * FROM subtitle')
        row = cursor.fetchone()

        if row is None:
            return {"content": ''}

        subtitle = Subtitle(row[0])
        return {"content": subtitle.content}


@app.route('/playlist_index_swap', methods=['GET'])
@login_required
def pi_swap():
    one = int(request.args.get('one'))
    another = int(request.args.get('another'))

    with conn:
        # get one from database
        one_tuple = list(conn.execute('SELECT * FROM video where id=?', (one,)).fetchone())
        another_tuple = list(conn.execute('SELECT * FROM video where id=?', (another,)).fetchone())
        
        # delete those entries
        conn.execute('DELETE FROM video WHERE id=?', (one,))
        conn.execute('DELETE FROM video WHERE id=?', (another,))

        # swap id in tuples
        tmp = one_tuple[0]
        one_tuple[0] = another_tuple[0]
        another_tuple[0] = tmp

        # insert into database
        conn.execute('INSERT INTO video (id, filename, status) VALUES (?, ?, ?)', (one_tuple[0], one_tuple[1], one_tuple[2]))
        conn.execute('INSERT INTO video (id, filename, status) VALUES (?, ?, ?)', (another_tuple[0], another_tuple[1], another_tuple[2]))
        
        conn.commit()

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

            conn.execute('UPDATE video SET status = ? WHERE id = ?', ('unlisted', video_id))

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400


@app.route('/make_video_listed', methods=['GET'])
@login_required
def make_video_listed():
    try:
        video_id = int(request.args.get('id'))

        with conn:
            cursor = conn.execute('SELECT * FROM video WHERE id = ?', (video_id,))
            row = cursor.fetchone()

            if row is None:
                return {"message": "Invalid video ID"}

            conn.execute('UPDATE video SET status = ? WHERE id = ?', ('listed', video_id))

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

@app.route('/upload_video', methods=['POST'])
@login_required
def upload_video():
    # check if the post request has the file part
    if 'video' not in request.files:
        return {"message": "No file part"}, 400

    file = request.files['video']
    # if user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        return {"message": "No selected file"}, 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn.execute('INSERT INTO video (filename, status) VALUES (?, ?)', (filename, 'listed'))
        return {"message": "success"}
    else:
        return {"message": "Invalid file format"}, 400

@app.route('/current_video', methods=['GET'])
@login_required
def current_video():
    return {"video": CURRENTLY_PLAYING_VIDEO_NAME}

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
    global CURRENTLY_PLAYING_VIDEO_NAME
    session['receive_count'] = session.get('receive_count', 0) + 1
    current_video_index = message['current_video_index']

    try:
        with conn:
            cursor = conn.execute('SELECT * FROM video ORDER BY id')
            videos = [Video(*row) for row in cursor.fetchall()]

            for video in videos:
                print(video.filename)

            if len(videos) == 0:
                raise Exception("No videos in the local store")

            traversing = -1
            while traversing < len(videos):
                traversing += 1
                current_video_index += 1
                if current_video_index >= len(videos) or current_video_index < 0:
                    current_video_index = 0

                next_video = videos[current_video_index]
                if next_video.status != 'unlisted':
                    emit('next_video', {'video_id': current_video_index, 'video_name': next_video.filename})
                    socket_.emit('next_video', {'video_id': current_video_index, 'video_name': next_video.filename}, namespace='/admin-video')
                    CURRENTLY_PLAYING_VIDEO_NAME = next_video.filename
                    break

    except Exception as e:
        print(traceback.format_exc())


@socket_.on('next_video', namespace='/admin-video')
@login_required
def admin_play_video(message):
    global CURRENTLY_PLAYING_VIDEO_NAME
    session['receive_count'] = session.get('receive_count', 0) + 1
    current_video_index = message['current_video_index']

    try:
        with conn:
            cursor = conn.execute('SELECT * FROM video ORDER BY id')
            videos = [Video(*row) for row in cursor.fetchall()]

            for video in videos:
                print(video.filename)

            if len(videos) == 0:
                raise Exception("No videos in the local store")

            traversing = -1
            while traversing < len(videos):
                traversing += 1
                current_video_index += 1
                if current_video_index >= len(videos) or current_video_index < 0:
                    current_video_index = 0

                next_video = videos[current_video_index]
                
                emit('next_video', {'video_id': current_video_index, 'video_name': next_video.filename})
                socket_.emit('next_video', {'video_id': current_video_index, 'video_name': next_video.filename}, namespace='/video')
                CURRENTLY_PLAYING_VIDEO_NAME = next_video.filename
                break

    except Exception as e:
        print(traceback.format_exc())

@socket_.on("play_pause", namespace='/admin-video')
@login_required
def play_pause():
    socket_.emit('play_pause', namespace='/video')

@socket_.on('connect', namespace='/video')
@login_required
def send_play_command():
    try:
        emit('play_pause', {'data': 'play_pause'})
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
        
        # check if the url contains a next parameter
        next = request.args.get('next')
        print("next:", next)
        if next != None and next != '':
            return redirect(next)

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

