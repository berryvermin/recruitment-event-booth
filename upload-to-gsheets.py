# Should be exported as a standalone executable
# Can be done by running: pyinstaller --onefile --console --clean upload-to-gsheets.py

import requests
import time

url = "https://script.google.com/macros/s/AKfycbyUeNjw-wHF3ODJ8TyBLEv41bUDjciQFqEs-wXTWizN1E8xFT3KzA9a11YNHTarRBxUPw/exec"

time_value = 72.34

timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
minutes = int(time_value // 60)
seconds = int(time_value % 60)
hundredths = int((time_value * 100) % 100)
formatted_time = f"{minutes:02}:{seconds:02}:{hundredths:02}"

payload = {
    "sheet": "Track",
    "action": "add",
    "values": {
        "Timestamp": timestamp,
        "Name": "Berry",
        "E-mail": "berry@example.com",
        "Track": "Track 1",
        "Time": formatted_time,
    }
}
headers = {
    "Content-Type": "application/json",
}

response = requests.request("POST", url, json=payload, headers=headers)