# Digital Broadcasting Display

Digital Broadcasting Display is a Flask-based web application designed for managing and displaying a collection of videos on a digital display. It provides an admin interface for managing the video playlist and a viewer interface for displaying the videos. This README file provides an overview of the application and its features.

## Features

### User Authentication
- Users can log in to the admin interface using a username and password.
- User authentication is handled using Flask-Login, ensuring secure access to admin functionalities.

### Video Management
- Admin users can upload videos to the system.
- Uploaded videos are stored in the 'videos' directory.
- Videos can be listed or unlisted, allowing control over whether they appear in the public viewer interface.

### Playlist Management
- Admin users can reorder the playlist by swapping the positions of videos.
- Videos can be made listed or unlisted to control their visibility in the playlist.

### Real-time Subtitles
- Admin users can update and display subtitles in real-time for the currently playing video.

### Video Playback Control
- Admin users can play and pause the currently displayed video.
- The viewer interface displays the currently playing video.

### Cross-Origin Resource Sharing (CORS)
- The application includes CORS headers to enable cross-origin requests, allowing integration with other web applications.

### Permanent Sessions
- User sessions are set to be permanent, with a session lifetime of 4 years.

## Getting Started
1. Clone the repository to your local machine.
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Create a folder named 'videos' in the root directory to store uploaded videos.
4. Run the application using `python main.py`.

## Usage
- Access the admin interface by navigating to `/admin` in your web browser. Log in using your credentials.
- Use the admin interface to upload videos, manage the playlist, and control video playback.
- View the video display interface by navigating to the root URL `/` after logging in as an admin or by opening it in a separate browser window.
- Admin users can control video playback and subtitles in real-time from the admin interface.

## Supported Video Formats
- The application supports the following video formats: mp4, avi, and mov.

## Disclaimer
This application is designed for educational and demonstration purposes. Ensure that you have the appropriate rights and permissions to display and manage the videos used in this application.

## License
I currently don't know about software licensing. Just contact me before using any of this code in your public or private project.

## Authors
- [MS-Jahan](https://github.com/MS-Jahan/Digital-Broadcasting-Display)

Feel free to create issues.
