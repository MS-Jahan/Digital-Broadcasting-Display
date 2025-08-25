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


class PlaylistItem:
    def __init__(self, id, type, content, status, duration, font_size, text_color, bg_color):
        self.id = id
        self.type = type
        self.content = content
        self.status = status
        self.duration = duration
        self.font_size = font_size
        self.text_color = text_color
        self.bg_color = bg_color

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

    # Create the playlist_item table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS playlist_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL,
            duration INTEGER,
            font_size TEXT,
            text_color TEXT,
            bg_color TEXT,
            position_x TEXT DEFAULT 'center',
            position_y TEXT DEFAULT 'center',
            alignment TEXT DEFAULT 'center'
        )
    ''')

    # Create the subtitle table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS subtitle (
            content TEXT NOT NULL
        )
    ''')

    # Create the user table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create the logo_settings table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS logo_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logo_path TEXT,
            position_x TEXT DEFAULT 'right',
            position_y TEXT DEFAULT 'top',
            offset_x INTEGER DEFAULT 30,
            offset_y INTEGER DEFAULT 30,
            width INTEGER DEFAULT 100,
            height INTEGER DEFAULT 100,
            animation TEXT DEFAULT 'rotate'
        )
    ''')

    # Create the token_counter table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS token_counter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'Token Counter',
            current_value INTEGER DEFAULT 0,
            font_size TEXT DEFAULT '72px',
            text_color TEXT DEFAULT '#FFFFFF',
            bg_color TEXT DEFAULT 'rgba(0, 0, 0, 0.7)',
            bg_image_path TEXT,
            position_x TEXT DEFAULT 'center',
            position_y TEXT DEFAULT 'center',
            animation TEXT DEFAULT 'fade',
            is_active BOOLEAN DEFAULT 0
        )
    ''')

    # Create the live_stream table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS live_stream (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'Live Stream',
            stream_type TEXT DEFAULT 'camera', -- 'camera', 'screen'
            is_active BOOLEAN DEFAULT 0,
            position_x TEXT DEFAULT 'center',
            position_y TEXT DEFAULT 'center',
            width TEXT DEFAULT '80%',
            height TEXT DEFAULT '80%',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # create a default user if it doesn't exist
    with conn:
        cursor = conn.execute('SELECT * FROM user WHERE username = ?', ('admin',))
        row = cursor.fetchone()

        if row is None:
            conn.execute('INSERT INTO user (username, password) VALUES (?, ?)', ('admin', 'admin'))

    subtitle_entry = Subtitle('')

    # Populate the playlist_item table
    with conn:
        cursor = conn.execute("SELECT content FROM playlist_item WHERE type = 'video'")
        existing_videos = set(row[0] for row in cursor.fetchall())

        videos = os.listdir(app.config['VIDEO_FOLDER'])

        # delete any non-existing videos
        for video in existing_videos:
            if video not in videos:
                print("[+] Deleting video: " + video)
                conn.execute("DELETE FROM playlist_item WHERE content = ? AND type = 'video'", (video,))

        for video in videos:
            if video not in existing_videos:
                print("[+] Adding video: " + video)
                conn.execute("INSERT INTO playlist_item (type, content, status) VALUES ('video', ?, 'listed')", (video,))
        


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

@app.route('/mobile')
@login_required
def mobile_stream():
    """Mobile streaming client page"""
    return render_template('mobile_stream.html')


@app.route('/api/playlist_items')
@login_required
def all_playlist_items():
    cursor = conn.execute('SELECT * FROM playlist_item')
    items = [dict(row) for row in cursor.fetchall()]
    return {"items": items}


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


@app.route('/api/playlist_item/swap', methods=['GET'])
@login_required
def pi_swap():
    one = int(request.args.get('one'))
    another = int(request.args.get('another'))

    with conn:
        # get one from database
        one_tuple = list(conn.execute('SELECT * FROM playlist_item where id=?', (one,)).fetchone())
        another_tuple = list(conn.execute('SELECT * FROM playlist_item where id=?', (another,)).fetchone())
        
        # delete those entries
        conn.execute('DELETE FROM playlist_item WHERE id=?', (one,))
        conn.execute('DELETE FROM playlist_item WHERE id=?', (another,))

        # swap id in tuples
        tmp = one_tuple[0]
        one_tuple[0] = another_tuple[0]
        another_tuple[0] = tmp

        # insert into database
        conn.execute('INSERT INTO playlist_item (id, type, content, status, duration, font_size, text_color, bg_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', tuple(one_tuple))
        conn.execute('INSERT INTO playlist_item (id, type, content, status, duration, font_size, text_color, bg_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', tuple(another_tuple))
        
        conn.commit()

    return {"message": "success"}


@app.route('/api/playlist_item/unlisted', methods=['GET'])
@login_required
def make_item_unlisted():
    try:
        item_id = int(request.args.get('id'))

        with conn:
            cursor = conn.execute('SELECT * FROM playlist_item WHERE id = ?', (item_id,))
            row = cursor.fetchone()

            if row is None:
                return {"message": "Invalid item ID"}

            conn.execute('UPDATE playlist_item SET status = ? WHERE id = ?', ('unlisted', item_id))

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400


@app.route('/api/playlist_item/listed', methods=['GET'])
@login_required
def make_item_listed():
    try:
        item_id = int(request.args.get('id'))

        with conn:
            cursor = conn.execute('SELECT * FROM playlist_item WHERE id = ?', (item_id,))
            row = cursor.fetchone()

            if row is None:
                return {"message": "Invalid item ID"}

            conn.execute('UPDATE playlist_item SET status = ? WHERE id = ?', ('listed', item_id))

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400


@app.route('/api/playlist_item/delete', methods=['GET'])
@login_required
def delete_playlist_item():
    try:
        item_id = int(request.args.get('id'))

        with conn:
            cursor = conn.execute('SELECT * FROM playlist_item WHERE id = ?', (item_id,))
            item = cursor.fetchone()

            if item is None:
                return {"message": "Invalid item ID"}

            if item['type'] == 'video':
                video_path = os.path.join(app.config['VIDEO_FOLDER'], item['content'])
                os.remove(video_path)

            conn.execute('DELETE FROM playlist_item WHERE id = ?', (item_id,))

        return {"message": "success"}
    except Exception as e:
        return {"message": str(e)}, 400

@app.route('/api/playlist_item/upload_video', methods=['POST'])
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
        conn.execute("INSERT INTO playlist_item (type, content, status) VALUES ('video', ?, 'listed')", (filename,))
        return {"message": "success"}
    else:
        return {"message": "Invalid file format"}, 400

@app.route('/api/playlist_item/add_notice', methods=['POST'])
@login_required
def add_notice():
    data = request.json
    content = data.get('content')
    duration = data.get('duration')
    font_size = data.get('font_size')
    text_color = data.get('text_color')
    bg_color = data.get('bg_color')
    position_x = data.get('position_x', 'center')
    position_y = data.get('position_y', 'center')
    alignment = data.get('alignment', 'center')

    with conn:
        conn.execute(
            "INSERT INTO playlist_item (type, content, status, duration, font_size, text_color, bg_color, position_x, position_y, alignment) VALUES ('notice', ?, 'listed', ?, ?, ?, ?, ?, ?, ?)",
            (content, duration, font_size, text_color, bg_color, position_x, position_y, alignment)
        )
        conn.commit()

    return {"message": "success"}


@app.route('/api/playlist_item/add_image_notice', methods=['POST'])
@login_required
def add_image_notice():
    # check if the post request has the file part
    if 'image' not in request.files:
        return {"message": "No file part"}, 400

    file = request.files['image']
    # if user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        return {"message": "No selected file"}, 400

    if file:
        filename = secure_filename(file.filename)
        if not os.path.exists('uploads/images'):
            os.makedirs('uploads/images')
        file.save(os.path.join('uploads/images', filename))

        duration = request.form.get('duration')

        with conn:
            conn.execute(
                "INSERT INTO playlist_item (type, content, status, duration) VALUES ('image', ?, 'listed', ?)",
                (filename, duration)
            )
            conn.commit()

        return {"message": "success"}
    else:
        return {"message": "Invalid file format"}, 400


@app.route('/current_video', methods=['GET'])
@login_required
def current_video():
    return {"video": CURRENTLY_PLAYING_VIDEO_NAME}

@app.route('/api/logo/upload', methods=['POST'])
@login_required
def upload_logo():
    # check if the post request has the file part
    if 'logo' not in request.files:
        return {"message": "No file part"}, 400

    file = request.files['logo']
    if file.filename == '':
        return {"message": "No selected file"}, 400

    if file:
        filename = secure_filename(file.filename)
        if not os.path.exists('static/logos'):
            os.makedirs('static/logos')
        file.save(os.path.join('static/logos', filename))

        # Update logo settings in database
        with conn:
            cursor = conn.execute('SELECT * FROM logo_settings ORDER BY id DESC LIMIT 1')
            existing = cursor.fetchone()
            
            if existing is None:
                conn.execute(
                    "INSERT INTO logo_settings (logo_path) VALUES (?)",
                    (f'logos/{filename}',)
                )
            else:
                conn.execute(
                    "UPDATE logo_settings SET logo_path = ? WHERE id = ?",
                    (f'logos/{filename}', existing[0])
                )
            conn.commit()

        return {"message": "success"}
    else:
        return {"message": "Invalid file format"}, 400

@app.route('/api/logo/settings', methods=['GET'])
@login_required
def get_logo_settings():
    with conn:
        cursor = conn.execute('SELECT * FROM logo_settings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        
        if row is None:
            return {"logo_path": "ist_logo.png", "position_x": "right", "position_y": "top", 
                   "offset_x": 30, "offset_y": 30, "width": 100, "height": 100, "animation": "rotate"}
        
        return {
            "logo_path": row[1] or "ist_logo.png",
            "position_x": row[2],
            "position_y": row[3],
            "offset_x": row[4],
            "offset_y": row[5],
            "width": row[6],
            "height": row[7],
            "animation": row[8]
        }

@app.route('/api/logo/settings', methods=['POST'])
@login_required
def update_logo_settings():
    data = request.json
    position_x = data.get('position_x', 'right')
    position_y = data.get('position_y', 'top')
    offset_x = data.get('offset_x', 30)
    offset_y = data.get('offset_y', 30)
    width = data.get('width', 100)
    height = data.get('height', 100)
    animation = data.get('animation', 'rotate')

    with conn:
        cursor = conn.execute('SELECT * FROM logo_settings ORDER BY id DESC LIMIT 1')
        existing = cursor.fetchone()
        
        if existing is None:
            conn.execute(
                "INSERT INTO logo_settings (position_x, position_y, offset_x, offset_y, width, height, animation) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (position_x, position_y, offset_x, offset_y, width, height, animation)
            )
        else:
            conn.execute(
                "UPDATE logo_settings SET position_x = ?, position_y = ?, offset_x = ?, offset_y = ?, width = ?, height = ?, animation = ? WHERE id = ?",
                (position_x, position_y, offset_x, offset_y, width, height, animation, existing[0])
            )
        conn.commit()

    return {"message": "success"}

@app.route('/api/token/counter', methods=['GET'])
@login_required
def get_token_counter():
    with conn:
        cursor = conn.execute('SELECT * FROM token_counter ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        
        if row is None:
            return {"name": "Token Counter", "current_value": 0, "font_size": "72px", 
                   "text_color": "#FFFFFF", "bg_color": "rgba(0, 0, 0, 0.7)", 
                   "bg_image_path": None, "position_x": "center", "position_y": "center", 
                   "animation": "fade", "is_active": False}
        
        return {
            "name": row[1],
            "current_value": row[2],
            "font_size": row[3],
            "text_color": row[4],
            "bg_color": row[5],
            "bg_image_path": row[6],
            "position_x": row[7],
            "position_y": row[8],
            "animation": row[9],
            "is_active": bool(row[10])
        }

@app.route('/api/token/counter', methods=['POST'])
@login_required
def update_token_counter():
    data = request.json
    name = data.get('name', 'Token Counter')
    font_size = data.get('font_size', '72px')
    text_color = data.get('text_color', '#FFFFFF')
    bg_color = data.get('bg_color', 'rgba(0, 0, 0, 0.7)')
    position_x = data.get('position_x', 'center')
    position_y = data.get('position_y', 'center')
    animation = data.get('animation', 'fade')
    is_active = data.get('is_active', False)

    with conn:
        cursor = conn.execute('SELECT * FROM token_counter ORDER BY id DESC LIMIT 1')
        existing = cursor.fetchone()
        
        if existing is None:
            conn.execute(
                "INSERT INTO token_counter (name, font_size, text_color, bg_color, position_x, position_y, animation, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, font_size, text_color, bg_color, position_x, position_y, animation, is_active)
            )
        else:
            conn.execute(
                "UPDATE token_counter SET name = ?, font_size = ?, text_color = ?, bg_color = ?, position_x = ?, position_y = ?, animation = ?, is_active = ? WHERE id = ?",
                (name, font_size, text_color, bg_color, position_x, position_y, animation, is_active, existing[0])
            )
        conn.commit()

    return {"message": "success"}

@app.route('/api/token/increment', methods=['POST'])
@login_required
def increment_token_counter():
    with conn:
        cursor = conn.execute('SELECT * FROM token_counter ORDER BY id DESC LIMIT 1')
        existing = cursor.fetchone()
        
        if existing is None:
            conn.execute("INSERT INTO token_counter (current_value) VALUES (1)")
            new_value = 1
        else:
            new_value = existing[2] + 1
            conn.execute("UPDATE token_counter SET current_value = ? WHERE id = ?", (new_value, existing[0]))
        conn.commit()
    
    # Emit socket event to update frontend
    socket_.emit('token_updated', {'current_value': new_value}, namespace='/video')
    
    return {"message": "success", "current_value": new_value}

@app.route('/api/token/decrement', methods=['POST'])
@login_required
def decrement_token_counter():
    with conn:
        cursor = conn.execute('SELECT * FROM token_counter ORDER BY id DESC LIMIT 1')
        existing = cursor.fetchone()
        
        if existing is None:
            conn.execute("INSERT INTO token_counter (current_value) VALUES (0)")
            new_value = 0
        else:
            new_value = max(0, existing[2] - 1)  # Don't allow negative values
            conn.execute("UPDATE token_counter SET current_value = ? WHERE id = ?", (new_value, existing[0]))
        conn.commit()
    
    # Emit socket event to update frontend
    socket_.emit('token_updated', {'current_value': new_value}, namespace='/video')
    
    return {"message": "success", "current_value": new_value}

@app.route('/api/token/reset', methods=['POST'])
@login_required
def reset_token_counter():
    with conn:
        cursor = conn.execute('SELECT * FROM token_counter ORDER BY id DESC LIMIT 1')
        existing = cursor.fetchone()
        
        if existing is None:
            conn.execute("INSERT INTO token_counter (current_value) VALUES (0)")
        else:
            conn.execute("UPDATE token_counter SET current_value = 0 WHERE id = ?", (existing[0],))
        conn.commit()
    
    # Emit socket event to update frontend
    socket_.emit('token_updated', {'current_value': 0}, namespace='/video')
    
    return {"message": "success", "current_value": 0}

@app.route('/api/token/upload_bg', methods=['POST'])
@login_required
def upload_token_bg():
    if 'background' not in request.files:
        return {"message": "No file part"}, 400

    file = request.files['background']
    if file.filename == '':
        return {"message": "No selected file"}, 400

    if file:
        filename = secure_filename(file.filename)
        if not os.path.exists('static/token_backgrounds'):
            os.makedirs('static/token_backgrounds')
        file.save(os.path.join('static/token_backgrounds', filename))

        # Update token counter background in database
        with conn:
            cursor = conn.execute('SELECT * FROM token_counter ORDER BY id DESC LIMIT 1')
            existing = cursor.fetchone()
            
            if existing is None:
                conn.execute(
                    "INSERT INTO token_counter (bg_image_path) VALUES (?)",
                    (f'token_backgrounds/{filename}',)
                )
            else:
                conn.execute(
                    "UPDATE token_counter SET bg_image_path = ? WHERE id = ?",
                    (f'token_backgrounds/{filename}', existing[0])
                )
            conn.commit()

        return {"message": "success"}
    else:
        return {"message": "Invalid file format"}, 400

@app.route('/api/system/shutdown', methods=['POST'])
@login_required
def system_shutdown():
    """Remote shutdown - USE WITH CAUTION"""
    import subprocess
    import platform
    
    try:
        system = platform.system().lower()
        if system == 'windows':
            subprocess.Popen(['shutdown', '/s', '/t', '10'], shell=True)
        elif system in ['linux', 'darwin']:
            subprocess.Popen(['shutdown', '-h', '+1'], shell=True)
        else:
            return {"message": "Unsupported operating system"}, 400
        
        return {"message": "Shutdown initiated - system will shutdown in 1 minute"}
    except Exception as e:
        return {"message": f"Failed to initiate shutdown: {str(e)}"}, 500

@app.route('/api/system/restart', methods=['POST'])
@login_required
def system_restart():
    """Remote restart - USE WITH CAUTION"""
    import subprocess
    import platform
    
    try:
        system = platform.system().lower()
        if system == 'windows':
            subprocess.Popen(['shutdown', '/r', '/t', '10'], shell=True)
        elif system in ['linux', 'darwin']:
            subprocess.Popen(['shutdown', '-r', '+1'], shell=True)
        else:
            return {"message": "Unsupported operating system"}, 400
        
        return {"message": "Restart initiated - system will restart in 1 minute"}
    except Exception as e:
        return {"message": f"Failed to initiate restart: {str(e)}"}, 500

@app.route('/api/system/cancel_shutdown', methods=['POST'])
@login_required
def cancel_shutdown():
    """Cancel pending shutdown/restart"""
    import subprocess
    import platform
    
    try:
        system = platform.system().lower()
        if system == 'windows':
            subprocess.Popen(['shutdown', '/a'], shell=True)
        elif system in ['linux', 'darwin']:
            subprocess.Popen(['shutdown', '-c'], shell=True)
        else:
            return {"message": "Unsupported operating system"}, 400
        
        return {"message": "Shutdown/restart cancelled"}
    except Exception as e:
        return {"message": f"Failed to cancel shutdown: {str(e)}"}, 500

@app.route('/api/stream/settings', methods=['GET'])
@login_required
def get_stream_settings():
    with conn:
        cursor = conn.execute('SELECT * FROM live_stream ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        
        if row is None:
            return {"name": "Live Stream", "stream_type": "camera", "is_active": False,
                   "position_x": "center", "position_y": "center", "width": "80%", "height": "80%"}
        
        return {
            "name": row[1],
            "stream_type": row[2],
            "is_active": bool(row[3]),
            "position_x": row[4],
            "position_y": row[5],
            "width": row[6],
            "height": row[7]
        }

@app.route('/api/stream/settings', methods=['POST'])
@login_required
def update_stream_settings():
    data = request.json
    name = data.get('name', 'Live Stream')
    stream_type = data.get('stream_type', 'camera')
    is_active = data.get('is_active', False)
    position_x = data.get('position_x', 'center')
    position_y = data.get('position_y', 'center')
    width = data.get('width', '80%')
    height = data.get('height', '80%')

    with conn:
        cursor = conn.execute('SELECT * FROM live_stream ORDER BY id DESC LIMIT 1')
        existing = cursor.fetchone()
        
        if existing is None:
            conn.execute(
                "INSERT INTO live_stream (name, stream_type, is_active, position_x, position_y, width, height) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, stream_type, is_active, position_x, position_y, width, height)
            )
        else:
            conn.execute(
                "UPDATE live_stream SET name = ?, stream_type = ?, is_active = ?, position_x = ?, position_y = ?, width = ?, height = ?, last_active = CURRENT_TIMESTAMP WHERE id = ?",
                (name, stream_type, is_active, position_x, position_y, width, height, existing[0])
            )
        conn.commit()
    
    # Notify viewers about stream status change
    socket_.emit('stream_status_changed', {
        'is_active': is_active,
        'stream_type': stream_type,
        'position_x': position_x,
        'position_y': position_y,
        'width': width,
        'height': height
    }, namespace='/video')
    
    return {"message": "success"}

@app.route('/api/stream/start', methods=['POST'])
@login_required
def start_stream():
    data = request.json
    stream_type = data.get('stream_type', 'camera')
    
    with conn:
        cursor = conn.execute('SELECT * FROM live_stream ORDER BY id DESC LIMIT 1')
        existing = cursor.fetchone()
        
        if existing is None:
            conn.execute(
                "INSERT INTO live_stream (stream_type, is_active, last_active) VALUES (?, 1, CURRENT_TIMESTAMP)",
                (stream_type,)
            )
        else:
            conn.execute(
                "UPDATE live_stream SET stream_type = ?, is_active = 1, last_active = CURRENT_TIMESTAMP WHERE id = ?",
                (stream_type, existing[0])
            )
        conn.commit()
    
    # Notify viewers that stream is starting
    socket_.emit('stream_started', {'stream_type': stream_type}, namespace='/video')
    
    return {"message": "success", "stream_type": stream_type}

@app.route('/api/stream/stop', methods=['POST'])
@login_required
def stop_stream():
    with conn:
        cursor = conn.execute('SELECT * FROM live_stream ORDER BY id DESC LIMIT 1')
        existing = cursor.fetchone()
        
        if existing is not None:
            conn.execute(
                "UPDATE live_stream SET is_active = 0, last_active = CURRENT_TIMESTAMP WHERE id = ?",
                (existing[0],)
            )
            conn.commit()
    
    # Notify viewers that stream has stopped
    socket_.emit('stream_stopped', {}, namespace='/video')
    
    return {"message": "success"}

# WebSocket handlers for live streaming
@socket_.on('join_stream', namespace='/stream')
@login_required
def join_stream_room():
    """Client joins the streaming room"""
    emit('stream_joined', {'message': 'Connected to stream'})
    print(f"Client {request.sid} joined streaming room")

@socket_.on('stream_frame', namespace='/stream')
@login_required
def handle_stream_frame(data):
    """Handle incoming video frames from mobile devices"""
    try:
        # Validate frame data
        if 'frame_data' not in data or 'stream_type' not in data:
            emit('stream_error', {'error': 'Invalid frame data'})
            return
        
        frame_data = data['frame_data']
        stream_type = data['stream_type']  # 'camera' or 'screen'
        
        # Update stream activity in database
        with conn:
            cursor = conn.execute('SELECT * FROM live_stream ORDER BY id DESC LIMIT 1')
            existing = cursor.fetchone()
            
            if existing is None:
                conn.execute(
                    "INSERT INTO live_stream (stream_type, is_active, last_active) VALUES (?, 1, CURRENT_TIMESTAMP)",
                    (stream_type,)
                )
            else:
                conn.execute(
                    "UPDATE live_stream SET stream_type = ?, is_active = 1, last_active = CURRENT_TIMESTAMP WHERE id = ?",
                    (stream_type, existing[0])
                )
            conn.commit()
        
        # Broadcast frame to all viewers
        socket_.emit('live_frame', {
            'frame_data': frame_data,
            'stream_type': stream_type,
            'timestamp': data.get('timestamp')
        }, namespace='/video')
        
    except Exception as e:
        print(f"Error handling stream frame: {str(e)}")
        emit('stream_error', {'error': 'Failed to process frame'})

@socket_.on('stream_heartbeat', namespace='/stream')
@login_required
def handle_stream_heartbeat(data):
    """Handle heartbeat from streaming clients to keep connection alive"""
    try:
        # Update last activity
        with conn:
            cursor = conn.execute('SELECT * FROM live_stream ORDER BY id DESC LIMIT 1')
            existing = cursor.fetchone()
            
            if existing is not None:
                conn.execute(
                    "UPDATE live_stream SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
                    (existing[0],)
                )
                conn.commit()
        
        emit('heartbeat_ack', {'status': 'alive'})
        
    except Exception as e:
        print(f"Error handling heartbeat: {str(e)}")

@socket_.on('disconnect', namespace='/stream')
@login_required
def handle_stream_disconnect():
    """Handle client disconnect from streaming"""
    print(f"Stream client {request.sid} disconnected")
    
    # Set stream as inactive when client disconnects
    with conn:
        cursor = conn.execute('SELECT * FROM live_stream ORDER BY id DESC LIMIT 1')
        existing = cursor.fetchone()
        
        if existing is not None:
            conn.execute(
                "UPDATE live_stream SET is_active = 0, last_active = CURRENT_TIMESTAMP WHERE id = ?",
                (existing[0],)
            )
            conn.commit()
    
    # Notify viewers that stream has stopped
    socket_.emit('stream_stopped', {}, namespace='/video')

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


@socket_.on('next_item', namespace='/video')
@login_required
def next_item(message):
    global CURRENTLY_PLAYING_VIDEO_NAME
    session['receive_count'] = session.get('receive_count', 0) + 1
    current_item_index = message['current_item_index']

    try:
        with conn:
            cursor = conn.execute('SELECT * FROM playlist_item ORDER BY id')
            items = [dict(row) for row in cursor.fetchall()]

            if len(items) == 0:
                raise Exception("No items in the local store")

            traversing = -1
            while traversing < len(items):
                traversing += 1
                current_item_index += 1
                if current_item_index >= len(items) or current_item_index < 0:
                    current_item_index = 0

                next_item = items[current_item_index]
                if next_item['status'] != 'unlisted':
                    emit('next_item', {'item': next_item, 'index': current_item_index})
                    socket_.emit('next_item', {'item': next_item, 'index': current_item_index}, namespace='/admin-video')
                    if next_item['type'] == 'video':
                        CURRENTLY_PLAYING_VIDEO_NAME = next_item['content']
                    break

    except Exception as e:
        print(traceback.format_exc())


@socket_.on('admin_play_item', namespace='/admin-video')
@login_required
def admin_play_item(message):
    global CURRENTLY_PLAYING_VIDEO_NAME
    session['receive_count'] = session.get('receive_count', 0) + 1
    current_item_index = message['current_item_index']

    try:
        with conn:
            cursor = conn.execute('SELECT * FROM playlist_item ORDER BY id')
            items = [dict(row) for row in cursor.fetchall()]

            if len(items) == 0:
                raise Exception("No items in the local store")

            next_item = items[current_item_index]

            emit('next_item', {'item': next_item, 'index': current_item_index})
            socket_.emit('next_item', {'item': next_item, 'index': current_item_index}, namespace='/video')
            if next_item['type'] == 'video':
                CURRENTLY_PLAYING_VIDEO_NAME = next_item['content']

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
