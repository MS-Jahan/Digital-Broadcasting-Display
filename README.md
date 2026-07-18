# Digital Broadcasting Display

[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://docker.com)
[![Flask](https://img.shields.io/badge/Flask-2.3.2-green.svg)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Contact_Author-yellow.svg)](#license)

Digital Broadcasting Display is a **comprehensive Flask-based digital signage system** designed for managing and displaying multimedia content on digital displays. It features advanced capabilities including live video streaming, token counter systems, remote device management, and real-time content control.

<!-- screenshot: docs/screenshots/hero.png -->

## Links

- **Repo:** https://github.com/MS-Jahan/Digital-Broadcasting-Display
- **Live demo:** self-hosted only — after Docker start, open [http://localhost:8082](http://localhost:8082)

## Tech Stack

**Backend:** Python 3.11+, Flask, Flask-SocketIO, Flask-Login, Pony ORM · **Infra:** Docker, Docker Compose · **Realtime:** Socket.IO / Eventlet

## Dependencies

Primary Python packages (see `backend/requirements.txt` for pinned versions):

- Flask, Flask-Cors, Flask-Login, Flask-Session, Flask-SocketIO
- Pony ORM, Eventlet, python-socketio / python-engineio

Install locally with:

```bash
pip install -r backend/requirements.txt
```

## 🚀 Quick Start with Docker

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (2.0+)

### One-Command Setup
```bash
# Clone the repository
git clone https://github.com/MS-Jahan/Digital-Broadcasting-Display.git
cd Digital-Broadcasting-Display

# Set up and start the application
./scripts/docker-manage.sh setup
./scripts/docker-manage.sh start
```

**🎉 That's it!** Access your application at [http://localhost:8082](http://localhost:8082)

**Default credentials:** Username: `admin`, Password: `admin` (⚠️ Change these in production!)

## 📱 Key Features

### 🎥 **Video & Media Management**
- **Multi-format video support**: MP4, AVI, MOV
- **Dynamic playlist management** with drag-and-drop reordering
- **Image notices** with customizable duration
- **Text notices** with full RGBA color and positioning control
- **Auto-detection** of new videos in the media directory

### 📱 **Live Video Streaming**
- **Mobile camera streaming** (front/back camera switching)
- **Screen sharing** from mobile devices
- **Real-time WebSocket** communication
- **10 FPS streaming** optimized for reasonable bandwidth
- **Configurable positioning** and sizing on display

### 🏦 **Token Counter System**
- **Bank-style digital counter** with large number display
- **Increment/Decrement/Reset** controls
- **Real-time updates** via Socket.IO
- **Custom backgrounds** and animations
- **Positioning and styling** customization

### 🎨 **Advanced Customization**
- **Logo management** with upload and positioning
- **Notice positioning** (top, center, bottom)
- **RGBA color support** for text and backgrounds
- **Animation effects** for logos and counters
- **Responsive design** for both admin and viewer interfaces

### 🔧 **Remote Management**
- **System shutdown/restart** with safety delays
- **Real-time subtitle updates** with marquee scrolling
- **Cross-origin resource sharing** (CORS) enabled
- **Session management** with 4-year lifetime
- **Multi-user admin support** (2-3 concurrent users)

### 🔒 **Security & Authentication**
- **Flask-Login** authentication system
- **Rate limiting** on login and API endpoints
- **Secure file uploads** with validation
- **Non-root container execution**
- **Security headers** via Nginx proxy

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin Panel   │    │  Viewer Display │    │ Mobile Streamer │
│   (Material UI) │    │  (Full-screen)  │    │   (Camera/Screen) │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
              ┌─────────────────────────────────────┐
              │          Flask Backend              │
              │  ┌─────────────────────────────┐    │
              │  │       Socket.IO Hub         │    │
              │  │  (/video, /admin, /stream)  │    │
              │  └─────────────────────────────┘    │
              │  ┌─────────────────────────────┐    │
              │  │      SQLite Database       │    │
              │  │   (Playlists, Settings,    │    │
              │  │    Tokens, Streams)        │    │
              │  └─────────────────────────────┘    │
              └─────────────────────────────────────┘
                                 │
                   ┌─────────────────────────────┐
                   │      File Storage           │
                   │   Videos | Images | Logos   │
                   │   Uploads | Backgrounds     │
                   └─────────────────────────────┘
```

## 🐳 Docker Deployment

### Production Deployment

```bash
# 1. Set up environment
./scripts/docker-manage.sh setup

# 2. Edit configuration
vim .env  # Update SECRET_KEY, admin credentials, etc.

# 3. Deploy with production services
docker-compose --profile production up -d

# 4. Enable automatic updates (optional)
docker-compose --profile auto-update up -d
```

### Services Included

| Service | Description | Profile |
|---------|-------------|----------|
| **app** | Main Flask application | default |
| **db_backup** | Automated database backups | default |
| **nginx** | Reverse proxy with SSL support | production |
| **watchtower** | Automatic container updates | auto-update |

### Management Commands

```bash
# Application lifecycle
./scripts/docker-manage.sh start      # Start services
./scripts/docker-manage.sh stop       # Stop services
./scripts/docker-manage.sh restart    # Restart services
./scripts/docker-manage.sh status     # Show status

# Maintenance
./scripts/docker-manage.sh logs       # View logs
./scripts/docker-manage.sh logs -f    # Follow logs
./scripts/docker-manage.sh shell      # Open container shell
./scripts/docker-manage.sh backup     # Manual backup
./scripts/docker-manage.sh update     # Update and restart
./scripts/docker-manage.sh clean      # Clean Docker resources

# Development
./scripts/docker-manage.sh build      # Build custom image
./scripts/docker-manage.sh reset      # ⚠️ Reset everything
```

## 💻 Local Development

### Native Python Setup
```bash
# Clone repository
git clone https://github.com/MS-Jahan/Digital-Broadcasting-Display.git
cd Digital-Broadcasting-Display/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create videos directory
mkdir -p videos

# Run application
python main.py
```

### Development with Docker
```bash
# Build and run in development mode
docker-compose -f docker-compose.yml up --build

# With file watching (requires volume mounts)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 📱 Mobile Live Streaming

### Setup Mobile Streaming
1. **Start the application** and ensure it's accessible on your network
2. **On your mobile device**, navigate to `http://YOUR_SERVER_IP:8082/mobile`
3. **Log in** with admin credentials
4. **Choose streaming type**:
   - 📹 **Camera**: Stream from front/back camera
   - 🖥️ **Screen Share**: Share your mobile screen
5. **Configure position** via admin panel settings

### Mobile Client Features
- **Front/back camera switching**
- **Mirror toggle** for selfie mode
- **Connection status** indicators
- **Optimized for mobile browsers**
- **Automatic reconnection**

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Flask environment mode |
| `SECRET_KEY` | `secret!` | Flask secret key (⚠️ Change this!) |
| `ADMIN_USERNAME` | `admin` | Default admin username |
| `ADMIN_PASSWORD` | `admin` | Default admin password |
| `HOST_PORT` | `8082` | External port mapping |
| `DATABASE_PATH` | `/app/data/database.sqlite` | Database file location |
| `BACKUP_INTERVAL` | `86400` | Backup interval (seconds) |
| `BACKUP_RETENTION` | `7` | Days to keep backups |

### Volume Mounts

| Volume | Purpose | Persistent |
|--------|---------|------------|
| `dbd_app_data` | Database and application data | ✅ Yes |
| `dbd_videos` | Video files | ✅ Yes |
| `dbd_uploads` | Uploaded images | ✅ Yes |
| `dbd_logos` | Custom logos | ✅ Yes |
| `dbd_token_backgrounds` | Token counter backgrounds | ✅ Yes |
| `dbd_logs` | Application logs | ✅ Yes |
| `dbd_backups` | Database backups | ✅ Yes |

## 🌐 API Endpoints

### Authentication
- `POST /login` - User login
- `GET /logout` - User logout

### Playlist Management
- `GET /api/playlist_items` - List all items
- `GET /api/playlist_item/swap?one=X&another=Y` - Reorder items
- `POST /api/playlist_item/upload_video` - Upload video
- `POST /api/playlist_item/add_notice` - Add text notice
- `POST /api/playlist_item/add_image_notice` - Add image notice

### Live Streaming
- `GET/POST /api/stream/settings` - Stream configuration
- `POST /api/stream/start` - Start streaming
- `POST /api/stream/stop` - Stop streaming

### Token Counter
- `GET/POST /api/token/counter` - Counter settings
- `POST /api/token/increment` - Increment counter
- `POST /api/token/decrement` - Decrement counter
- `POST /api/token/reset` - Reset counter

### System Control
- `POST /api/system/shutdown` - Remote shutdown (⚠️ Dangerous)
- `POST /api/system/restart` - Remote restart (⚠️ Dangerous)
- `POST /api/system/cancel_shutdown` - Cancel pending shutdown

### Logo Management
- `POST /api/logo/upload` - Upload logo
- `GET/POST /api/logo/settings` - Logo configuration

## 🔍 Monitoring & Maintenance

### Health Monitoring
```bash
# Check application health
curl -f http://localhost:8082/login

# Check container health
docker ps --filter name=dbd-app --format "table {{.Names}}\t{{.Status}}"

# View detailed container info
docker inspect dbd-app
```

### Log Management
```bash
# View all logs
./scripts/docker-manage.sh logs

# Follow specific service
docker-compose logs -f app

# Check log file size
du -h /var/lib/docker/volumes/dbd_logs/_data/
```

### Database Backup & Restore
```bash
# Manual backup
./scripts/docker-manage.sh backup

# List available backups
docker exec dbd-backup ls -la /backups/

# Restore from backup (replace TIMESTAMP)
docker exec -it dbd-app cp /backups/database_backup_TIMESTAMP.sqlite.gz /app/data/
gunzip /app/data/database_backup_TIMESTAMP.sqlite.gz
mv /app/data/database_backup_TIMESTAMP.sqlite /app/data/database.sqlite
```

## 🛡️ Security Considerations

### Production Checklist
- [ ] **Change default admin credentials**
- [ ] **Set secure SECRET_KEY** (32+ random characters)
- [ ] **Enable HTTPS** with SSL certificates
- [ ] **Configure firewall** rules
- [ ] **Regular security updates**
- [ ] **Monitor access logs**
- [ ] **Backup encryption** for sensitive data

### Nginx Security Headers
The included Nginx configuration automatically adds:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: no-referrer-when-downgrade`

## 🎯 Use Cases

### **Digital Signage**
- Corporate lobbies and waiting areas
- Retail stores and restaurants
- Educational institutions
- Healthcare facilities

### **Live Broadcasting**
- Event streaming from mobile devices
- Security monitoring displays
- Conference room presentations
- Remote content management

### **Queue Management**
- Bank token systems
- Hospital queue displays
- Service center management
- Appointment scheduling displays

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Digital-Broadcasting-Display.git

# Set up development environment
./scripts/docker-manage.sh setup

# Start in development mode
FLASK_ENV=development ./scripts/docker-manage.sh start
```

## 🐛 Troubleshooting

### Common Issues

**Port already in use**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8082
# Kill the process or change HOST_PORT in .env
```

**Permission denied on uploads**
```bash
# Fix volume permissions
docker exec -it dbd-app chown -R appuser:appuser /app/videos /app/uploads
```

**Database corruption**
```bash
# Restore from backup
./scripts/docker-manage.sh backup  # Create current backup first
# Then restore from previous backup as shown above
```

**Mobile streaming not working**
- Ensure both devices are on the same network
- Check firewall settings
- Try using IP address instead of localhost
- Verify camera/microphone permissions in browser

## 📄 License

This project is currently under **custom licensing terms**. Please **contact the author** before using any of this code in your public or private projects.

## 👨‍💻 Authors

- **MS-Jahan** - *Initial work and main development* - [@MS-Jahan](https://github.com/MS-Jahan)

## 🙏 Acknowledgments

- Flask and Flask-SocketIO communities
- Docker and containerization ecosystem
- Material Design UI components
- WebRTC and streaming technologies

---

**⭐ Star this repository if you find it useful!**

**🐛 Issues and suggestions are welcome!** Please check the [issues page](https://github.com/MS-Jahan/Digital-Broadcasting-Display/issues).
