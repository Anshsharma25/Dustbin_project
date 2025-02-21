import requests
import cv2
import numpy as np
import logging
import pickle
import os
from ultralytics import YOLO  # ✅ Import YOLO for model loading

logging.basicConfig(level=logging.INFO)

# Load YOLO models from pickle file
model_path = os.path.join(os.path.dirname(__file__), 'Models_pickle.pkl')

if not os.path.exists(model_path):
    logging.error(f"❌ Model file not found: {model_path}")
    raise FileNotFoundError("Models_pickle.pkl not found!")

with open(model_path, 'rb') as f:
    models = pickle.load(f)

# ✅ Load YOLO models correctly from .pt files
if 'polythene' in models and 'biogas' in models:
    polythene_model_path = models['polythene']
    biogas_model_path = models['biogas']

    if os.path.exists(polythene_model_path) and os.path.exists(biogas_model_path):
        model_polythene = YOLO(polythene_model_path)  # Load YOLO model
        model_biogas = YOLO(biogas_model_path)  # Load YOLO model
        logging.info("✅ YOLO models loaded successfully!")
    else:
        logging.error("❌ One or both YOLO model files (.pt) are missing!")
        raise FileNotFoundError("Check that both 'biogas.pt' and 'poly_non_poly.pt' exist in the project directory.")
else:
    logging.error(f"❌ Models_pickle.pkl is missing expected keys: {models.keys()}")
    raise KeyError("Models_pickle.pkl is missing expected keys: 'polythene' or 'biogas'")

# Updated flag mapping
class_to_flag = {
    "biogasready": 4,    # Biodegradable waste (ready for biogas)
    "nonbiogasready": 5, # Non-biodegradable waste
}

def capture_frame(cam_url):
    """Captures an image from the given camera URL."""
    try:
        resp = requests.get(cam_url, timeout=5)
        if resp.status_code == 200:
            arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return frame
        else:
            logging.error(f"❌ Camera request failed with status code {resp.status_code}")
    except requests.RequestException as e:
        logging.error(f"❌ Failed to fetch image from camera: {e}")
    return None

def detect_polythene(frame):
    """Detects polythene using YOLO."""
    if frame is None:
        logging.error("❌ Frame is empty! Skipping detection.")
        return False

    results = model_polythene.predict(frame)  # ✅ Use YOLO's predict method
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            detected_class = model_polythene.names[class_id]

            if "polythene" in detected_class.lower():
                logging.info("✅ Polythene detected!")
                return True
    logging.info("❌ No polythene detected.")
    return False

def detect_biodegradable(frame):
    """Detects whether waste is biogas-ready or not."""
    if frame is None:
        logging.error("❌ Frame is empty! Skipping detection.")
        return []

    results = model_biogas.predict(frame)  # ✅ Use YOLO's predict method
    detected_flags = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            detected_class = model_biogas.names[class_id]
            normalized_class = detected_class.lower().replace(" ", "")

            logging.info(f"🗑️ Detected Waste: {detected_class}")

            if normalized_class in class_to_flag:
                flag = class_to_flag[normalized_class]
                detected_flags.append(flag)
                logging.info(f"✅ Assigned Flag: {flag}")
            else:
                logging.warning(f"⚠️ Unrecognized class: {detected_class}")

    if detected_flags:
        selected_flag = min(detected_flags)  # Pick the lowest flag value
        logging.info(f"🚀 Sending Flag: {selected_flag}")
    else:
        logging.info("❌ No valid detections found.")
    
    return detected_flags

def send_command(command):
    """Sends commands to the hardware."""
    logging.info(f"⚙️ Sending Command: {command}")
    # Here, you would add actual hardware communication logic
