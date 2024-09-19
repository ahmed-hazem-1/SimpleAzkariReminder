import os
import requests
import time
import json
import random
import shutil
from plyer import notification
from pathlib import Path
import winreg as reg
import platform
import sys

documents_folder = Path(os.path.expanduser("~")) / "Documents"
azkari_folder = documents_folder / "Azkari Reminder"

if not azkari_folder.exists():
    azkari_folder.mkdir(parents=True, exist_ok=True)

local_file_path = azkari_folder / 'azkari.json'
icon_path = os.path.join(documents_folder, "Azkari Reminder", "icon.ico")


def get_resource_path(relative_path):
    """Get the absolute path to the resource, whether running as a script or executable."""
    relative_path = str(relative_path)  # Ensure relative_path is a string
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def ensure_icon_file():
    """Check if the icon file exists and copy it to the destination path if not."""
    if not os.path.exists(icon_path):
        bundled_icon_path = get_resource_path('icon.ico')
        if os.path.exists(bundled_icon_path):
            os.makedirs(os.path.dirname(icon_path), exist_ok=True)
            shutil.copy(bundled_icon_path, icon_path)
            print("Icon copied to:", icon_path)
        else:
            print("Bundled icon not found!")


ensure_icon_file()

Azkari_file = 'https://raw.githubusercontent.com/osamayy/azkar-db/master/azkar.json'

try:
    if not os.path.exists(local_file_path) or os.path.getsize(local_file_path) != int(
            requests.head(Azkari_file).headers['Content-Length']):
        with open(local_file_path, 'wb') as f:
            f.write(requests.get(Azkari_file).content)
except Exception as e:
    print(f"Error downloading or saving the file: {e}")

try:
    with open(local_file_path, 'r', encoding='utf-8') as file:
        azkar_data = json.load(file)
    if 'rows' in azkar_data:
        azkar_list = azkar_data['rows']
    else:
        raise ValueError("The expected 'rows' key is missing from the data")
except Exception as e:
    print(f"Error loading Azkari data: {e}")
    sys.exit(1)

random.shuffle(azkar_list)


def truncate_text(text, max_length):
    """Truncate text to fit within the maximum length, appending ellipsis if needed."""
    return text[:max_length] + ('...' if len(text) > max_length else '')


def show_notification(title, message):
    """Display a notification with the given title and message."""
    try:
        app_icon = icon_path if platform.system() == "Windows" and os.path.exists(icon_path) else None
        notification.notify(
            title=title,
            message=message,
            app_name="Azkari Reminder",
            timeout=15,
            app_icon=app_icon
        )
    except Exception as e:
        print(f"Error displaying notification: {e}")


def split_message(message, max_length):
    """Split message into chunks that fit within the maximum length, inserting new lines if needed."""
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]


def notify_long_message(zekr):
    if isinstance(zekr, list):
        if len(zekr) >= 6:
            title = f"{truncate_text(zekr[0], 64)}"  # Limit title to 64 characters
            message = f"{truncate_text(zekr[1], 2048)}\n\n{truncate_text(zekr[2], 2048)}"  # Allow longer messages
            for msg_chunk in split_message(message, 256):
                show_notification(title, msg_chunk)
                time.sleep(10)  # Small delay between chunks to avoid notification spam
        else:
            print(f"Unexpected data format: {zekr}")
    else:
        print(f"Unexpected data format: {zekr}")


def add_to_startup(executable_path):
    reg_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "AzkariReminder"
    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_key_path, 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(reg_key, app_name, 0, reg.REG_SZ, executable_path)
        reg.CloseKey(reg_key)
        print("Successfully added to startup!")
    except Exception as e:
        print(f"Failed to add to startup: {e}")
        import traceback
        traceback.print_exc()


exe_path = os.path.abspath(os.path.join(documents_folder, "Azkari Reminder", "azkari_reminder.exe"))

if os.path.exists(exe_path):
    add_to_startup(exe_path)
else:
    print("Executable not found. Please ensure it's correctly placed.")

while True:
    for zekr in azkar_list:
        notify_long_message(zekr)
        time.sleep(60)  # Wait for 1 minute before showing the next Azkar
