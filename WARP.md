# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Digital Broadcasting Display** application - a Flask-based web system for managing and displaying video playlists on digital displays. It features real-time video playback control, subtitle management, and multi-media content display (videos, images, notices) with Socket.IO for real-time communication.

## Architecture

### Backend Structure
- **Flask Application**: Main server (`backend/main.py`) with Socket.IO integration
- **SQLite Database**: Stores playlist items, subtitles, and user authentication data
- **File Storage**: Videos in `backend/videos/`, images in `backend/uploads/images/`
- **Authentication**: Flask-Login with default admin/admin credentials

### Frontend Components
- **Viewer Interface** (`/`): Full-screen video display with subtitle overlay
- **Admin Interface** (`/admin`): Material Design admin panel for playlist management
- **Real-time Communication**: Socket.IO namespaces (`/video`, `/admin-video`) for synchronization

### Key Data Models
```python
class PlaylistItem:
    # id, type (video/image/notice), content, status (listed/unlisted)
    # duration, font_size, text_color, bg_color

class User:
    # id, username, password (basic auth)

class Subtitle:
    # content (real-time subtitle text)
```

## Development Commands

### Environment Setup
```bash
cd backend
pip install -r requirements.txt
```

### Running the Application
```bash
cd backend
python main.py
# Server starts on port 8082
# Access viewer at: http://localhost:8082/
# Access admin at: http://localhost:8082/admin
```

### Database Management
- SQLite database (`database.sqlite`) is auto-created on first run
- Tables: `playlist_item`, `subtitle`, `user`
- Default admin user: username=`admin`, password=`admin`

### Content Management
- Videos: Place in `backend/videos/` directory (auto-detected)
- Images: Uploaded via admin interface to `backend/uploads/images/`
- Supported formats: mp4, avi, mov

## Key API Endpoints

### Playlist Management
- `GET /api/playlist_items` - List all playlist items
- `GET /api/playlist_item/swap?one=X&another=Y` - Reorder playlist
- `GET /api/playlist_item/listed?id=X` - Make item visible
- `GET /api/playlist_item/unlisted?id=X` - Hide item
- `POST /api/playlist_item/upload_video` - Upload video file
- `POST /api/playlist_item/add_notice` - Add text notice
- `POST /api/playlist_item/add_image_notice` - Add image notice

### Subtitle/Content Control
- `GET /subtitle` - Get current subtitle
- `POST /subtitle` - Update subtitle (broadcasts to viewers)

### Socket.IO Events
- `next_item` - Navigate to next playlist item
- `admin_play_item` - Admin-triggered item playback
- `play_pause` - Toggle playback state
- `subtitle_updated` - Real-time subtitle updates

## Configuration Notes

### Network Configuration
- Server URL auto-detection via `static/vars.js`
- CORS enabled for cross-origin requests
- Session lifetime: 4 years (development setting)

### File Structure
```
backend/
├── main.py              # Flask application entry point
├── vars.py              # Path configurations
├── templates/           # Jinja2 HTML templates
│   ├── index.html       # Viewer interface
│   ├── admin/index.html # Admin interface
│   └── login.html       # Authentication
├── static/              # JavaScript/CSS assets
│   ├── vars.js          # Server URL configuration
│   ├── playlist.js      # Playlist management functions
│   └── subtitle.js      # Subtitle control functions
├── videos/              # Video file storage (created automatically)
└── uploads/images/      # Uploaded image storage
```

## Testing Specific Features

### Video Playback Testing
```bash
# Add test video to videos directory
cp test_video.mp4 backend/videos/
# Restart server to auto-detect new videos
```

### Real-time Communication Testing
- Open viewer (`/`) and admin (`/admin`) in separate browser windows
- Test subtitle updates and playback control synchronization
- Verify Socket.IO connection in browser developer tools

### Database Reset
```bash
rm backend/database.sqlite
# Restart server to recreate with default admin user
```

## Production Deployment Notes

### Windows Startup Script
- `backend/ist_startup.bat` - Automated startup for Windows kiosk mode
- Launches Python server and Chrome in fullscreen mode
- Modify paths in script for your installation directory

### Security Considerations
- Change default admin credentials in production
- Consider implementing proper authentication system
- Review CORS settings for production environment
- SQLite suitable for single-instance deployment only

## Common Development Tasks

### Adding New Content Types
1. Extend `playlist_item` table schema in `startup_tasks()`
2. Update frontend rendering logic in `templates/index.html`
3. Add admin interface controls in `templates/admin/index.html`
4. Implement corresponding API endpoints

### Modifying Display Layout
- Edit `templates/index.html` for viewer interface
- Modify CSS in `templates/admin/index.html` for admin styling
- Update Socket.IO event handlers for new functionality

### Database Schema Changes
- Modify table creation in `startup_tasks()` function
- Add migration logic for existing databases if needed
- Update model classes to match schema changes
