from flask import Blueprint, jsonify
from helper import capture_frame, detect_polythene, detect_biodegradable, send_command
import time

garbage_bp = Blueprint("garbage", __name__)

# Define camera URLs
CAM_1 = "http://192.168.1.103/cam-hi.jpg"
CAM_2 = "http://192.168.1.104/cam-hi.jpg"

@garbage_bp.route("/process_garbage", methods=["GET"])
def process_garbage():
    """Processes garbage detection and sorting in a single request."""

    # Step 1: Capture Image from Camera 1
    frame1 = capture_frame(CAM_1)
    if frame1 is None:
        return jsonify({"error": "Failed to capture frame from CAM_1"}), 500

    # Step 2: Detect Polythene
    polythene_detected = detect_polythene(frame1)
    if polythene_detected:
        send_command('H')  # Hand pressure
        send_command('C')  # Cutter
        send_command('O')  # Open plate
    else:
        send_command('O')

    time.sleep(2)

    # Step 3: Capture Image from Camera 2
    frame2 = capture_frame(CAM_2)
    if frame2 is None:
        return jsonify({"error": "Failed to capture frame from CAM_2"}), 500

    # Step 4: Detect Biodegradable Garbage
    detected_flags = detect_biodegradable(frame2)

    # Step 5: Rotate Robotic Hand for Sorting
    if detected_flags:
        selected_flag = min(detected_flags)
        send_command(f"HAND_MOTOR:{selected_flag}")
        time.sleep(2)
        send_command("HAND_MOTOR:RESET")
        time.sleep(1)

    return jsonify({"message": "Garbage processing completed successfully"}), 200
