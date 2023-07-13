import os
from flask import Flask, render_template, session, copy_current_request_context, send_from_directory, request, redirect, url_for
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock
from pony.orm import *
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['VIDEO_FOLDER'] = 'videos'
socket_ = SocketIO(app)
thread = None
thread_lock = Lock()

# Configure Pony ORM
db = Database()


class Video(db.Entity):
    id = PrimaryKey(int, auto=True)
    filename = Required(str)
    status = Required(str)


class UnlistedVideo(db.Entity):
    id = PrimaryKey(int, auto=True)
    filename = Required(str)
    status = Required(str)


class User(UserMixin, db.Entity):
    id = PrimaryKey(int, auto=True)
    username = Required(str)
    password = Required(str)


db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
db.generate_mapping(create_tables=True)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    with db_session:
        return User.get(id=user_id)


def startup_tasks():
    if not os.path.exists(app.config['VIDEO_FOLDER']):
        os.mkdir(app.config['VIDEO_FOLDER'])

    # Populate the videos table
    with db_session:
        videos = os.listdir(app.config['VIDEO_FOLDER'])
        existing_videos = [v.filename for v in Video.select()]
        for video in videos:
            if video not in existing_videos:
                Video(filename=video, status='listed')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin')
@login_required
def admin():
    return render_template('admin/index.html')


@app.route('/all_videos')
@login_required
def all_videos():
    with db_session:
        videos = select(v for v in Video)[:]

    return {"videos": videos}


@app.route('/videos/<path:filename>')
@login_required
def videos(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)


@app.route('/playlist_index_swap', methods=['GET'])
@login_required
def pi_swap():
    one = int(request.args.get('one'))
    another = int(request.args.get('another'))

    with db_session:
        videos = select(v for v in Video).order_by(Video.id).limit(2, skip=one).for_update()
        if len(videos) != 2:
            return {"message": "Invalid indices"}

        videos[0].id, videos[1].id = videos[1].id, videos[0].id

    return {"message": "success"}


@app.route('/make_video_unlisted', methods=['GET'])
@login_required
def make_video_unlisted():
    try:
        video_id = int(request.args.get('id'))

        with db_session:
            video = Video.get(id=video_id)

            if video is None:
                return {"message": "Invalid video ID"}

            UnlistedVideo(filename=video.filename, status='unlisted')
            video.delete()

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400


@app.route('/make_video_listed', methods=['GET'])
@login_required
def make_video_listed():
    try:
        video_id = int(request.args.get('id'))

        with db_session:
            video = UnlistedVideo.get(id=video_id)

            if video is None:
                return {"message": "Invalid video ID"}

            Video(filename=video.filename, status='listed')
            video.delete()

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400


@app.route('/delete_video', methods=['GET'])
@login_required
def delete_video():
    try:
        video_id = int(request.args.get('id'))

        with db_session:
            video = Video.get(id=video_id)

            if video is None:
                return {"message": "Invalid video ID"}

            video_path = os.path.join(app.config['VIDEO_FOLDER'], video.filename)
            os.remove(video_path)
            video.delete()

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
        with db_session:
            videos = select(v for v in Video).order_by(Video.id)
            if len(videos) == 0:
                raise Exception("No videos in the local store")

            current_video_index += 1
            if current_video_index >= len(videos):
                current_video_index = 0

            next_video = videos[current_video_index]
            emit('next_video', {'video_id': next_video.id, 'video_name': next_video.filename})
    except Exception as e:
        raise e


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

        with db_session:
            user = User.get(username=username)

            if user is None or user.password != password:
                return redirect(url_for('login'))

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
    socket_.run(app, port=8082, debug=True)
