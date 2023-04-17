from flask import Flask, render_template, session, copy_current_request_context, send_from_directory
from flask_socketio import SocketIO, emit, disconnect

from threading import Lock

from helpers import *

startup_tasks()

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['VIDEO_FOLDER'] = VIDEOS_ROOT
socket_ = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


@app.route('/')
def index():
    return render_template('index.html', async_mode=socket_.async_mode)

@app.route('/videos/<path:filename>')
def videos(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)


@socket_.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socket_.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socket_.on('disconnect_request', namespace='/test')
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)

@socket_.on('next_video', namespace='/video')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    current_video_index = message['current_video_index']
    try:
        next_video = get_next_video(current_video_index)
        emit('next_video', next_video)
    except Exception as e:
        raise e

if __name__ == '__main__':
    socket_.run(app, debug=True)