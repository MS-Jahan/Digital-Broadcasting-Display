from flask import Flask, render_template, session, copy_current_request_context, send_from_directory, request
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

@app.route('/admin')
def admin():
    return render_template('admin/index.html', async_mode=socket_.async_mode)

@app.route('/all_videos')
def all_videos():
    return get_video_list()

@app.route('/videos/<path:filename>')
def videos(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

@app.route('/playlist_index_swap', methods=['GET'])
def pi_swap():
    one = int(request.args.get('one'))
    another = int(request.args.get('another'))
    return playlist_index_swap(one, another)

@app.route('/make_video_unlisted', methods=['GET'])
def make_video_unlisted():
    try:
        video_id = int(request.args.get('id'))
        with open(LOCAL_STORE_PATH, 'r') as f:
            local_store = json.load(f)

        local_store['unlisted_videos'].append(local_store["videos"][video_id])
        local_store["videos"].pop(video_id)
        
        with open(LOCAL_STORE_PATH, 'w') as f:
            json.dump(local_store, f, indent=4)
        
        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400

@app.route('/make_video_listed', methods=['GET'])
def make_video_listed():
    try:
        video_id = int(request.args.get('id'))
        with open(LOCAL_STORE_PATH, 'r') as f:
            local_store = json.load(f)

        local_store["videos"].append(local_store["unlisted_videos"][video_id])
        local_store["unlisted_videos"].pop(video_id)

        with open(LOCAL_STORE_PATH, 'w') as f:
            json.dump(local_store, f, indent=4)

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400

@app.route('/delete_video', methods=['GET'])
def delete_video():
    try:
        video_id = int(request.args.get('id'))
        with open(LOCAL_STORE_PATH, 'r') as f:
            local_store = json.load(f)

        os.remove(os.path.join(VIDEOS_ROOT, local_store["videos"][video_id]))

        local_store["videos"].pop(video_id)

        with open(LOCAL_STORE_PATH, 'w') as f:
            json.dump(local_store, f, indent=4)

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400

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
    
# on connect
@socket_.on('connect', namespace='/video')
def send_play_command():
    try:
        emit('play_video', {'data': 'play_video'})
    except Exception as e:
        raise e

if __name__ == '__main__':
    socket_.run(app, port=8082, debug=True)