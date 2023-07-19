@echo off

cd /d D:
cd D:\program\IST_Video_Screen\backend

start "" "..\..\python\python.exe" main.py

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --start-fullscreen --disable-session-crashed-bubble "http://localhost:8082"
