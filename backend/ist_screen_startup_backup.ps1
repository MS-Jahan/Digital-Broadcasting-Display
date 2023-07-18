cd D:
cd D:\program\IST_Video_Screen\backend
Start-Process -NoNewWindow ..\..\python\python.exe main.py

# start chrome:http://localhost:8082
Start-Process -FilePath "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList '--start-fullscreen --disable-session-crashed-bubble "http://localhost:8082"'
<# 
$wshell = New-Object -ComObject wscript.shell;
$wshell.AppActivate('chrome') 
while ($true)
{
    Sleep 2
    $wshell.SendKeys('{f11}')
    exit 
}

exit
#>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      