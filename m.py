from flask import Flask, jsonify, request
import cv2
import time
import requests
import numpy as np
import pickle
import threading
import logging

logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)   

# Load Pickle Model
with open("Models_pickle.pkl", "rb") as f:
    model_data = pickle.load(f)

ESP8266_IP_1 = "192.168.1.28"  # First ESP Module (Flag Sender)
ESP8266_IP_2 = "192.168.1.3"  # Second ESP Module (API Trigger)

class_to_flag = {
    'non-biodegradable': 1,
    'biodegradable': 2,
    'common': 3,
    'nonbiogasready': 5,
    'biogasready': 4
}

def send_command(cmd, esp_ip):
    url = f"http://{esp_ip}/command?value={cmd}"
    try:
        requests.get(url, timeout=5)
    except Exception as e:
        logging.error(f"Error communicating with ESP8266 at {esp_ip}: {e}")

def send_flag(flag):
    url = f"http://{ESP8266_IP_1}/flag?value={flag}"
    try:
        requests.get(url, timeout=5)
    except Exception as e:
        logging.error(f"Error communicating with ESP8266: {e}")

def capture_frame(cam_url):
    cap = cv2.VideoCapture(cam_url)
    time.sleep(2)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    cv2.imwrite("temp.jpg", frame)
    return frame

def detect_biodegradable(frame):
    detected_flags = []
    results = model_data.predict(frame)
    for detected_class in results:
        normalized_class = detected_class.lower().replace(" ", "-")
        flag = class_to_flag.get(normalized_class)
        if flag is not None:
            detected_flags.append(flag)
    if detected_flags:
        selected_flag = min(detected_flags)
        send_flag(selected_flag)
        return selected_flag
    return None

def process_garbage_task():
    while True:
        cam_1 = "http://192.168.1.103/cam-hi.jpg"
        cam_2 = "http://192.168.1.104/cam-hi.jpg"

        frame1 = capture_frame(cam_1)
        if frame1 is None:
            logging.error("Failed to capture frame from camera 1")
            continue

        for _ in range(4):
            send_command("MOVE", ESP8266_IP_2)
            time.sleep(1)
            frame2 = capture_frame(cam_2)
            if frame2 is None:
                continue
            detected_flag = detect_biodegradable(frame2)
            send_command(f"HAND_MOTOR:{detected_flag}" if detected_flag else "HAND_MOTOR:RESET", ESP8266_IP_2)
            time.sleep(2)
        
        logging.info("Process Completed Successfully")
        time.sleep(10)  # Interval before the next cycle

@app.route("/start_process", methods=["GET", "POST"])
def start_process():
    thread = threading.Thread(target=process_garbage_task, daemon=True)
    thread.start()
    return jsonify({"message": "Garbage processing started and will run continuously"})

@app.route("/receive_trigger", methods=["POST"])
def receive_trigger():
    data = request.json
    if not data or "trigger" not in data:
        return jsonify({"error": "Invalid request"}), 400
    
    if data["trigger"] == "start":
        thread = threading.Thread(target=process_garbage_task, daemon=True)
        thread.start()
        return jsonify({"message": "Garbage process triggered by ESP8266"})
    return jsonify({"error": "Invalid trigger command"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)