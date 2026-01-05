# main.py
import cv2
import mediapipe as mp
import time
import collections
import requests

from algorithm import calculate_ear, calculate_mar, head_nose_eye_ratio
from alerts import play_alarm, stop_alarm

# ---- CONFIG (tweak these for your camera / comfort) ----
SERVER_URL = "http://127.0.0.1:5000/update"   # dashboard endpoint
CALIBRATION_FRAMES = 40

# EAR (eye) settings
EAR_SMOOTH_WINDOW = 6
EAR_THRESH_FACTOR = 0.72   # EAR threshold = open_eye_ear * EAR_THRESH_FACTOR
EAR_CONSEC_FRAMES = 8      # sustained frames to trigger eye-close alert

# MAR (yawn) settings
MAR_SMOOTH_WINDOW = 6
MAR_THRESH = 0.70          # mouth aspect ratio threshold for yawn
MAR_CONSEC_FRAMES = 10     # sustained frames to trigger yawn alert

# HEAD TILT settings (relative ratio)
TILT_SMOOTH_WINDOW = 6
TILT_DELTA_RATIO = 0.08    # require ratio increase above baseline by this amount
TILT_VELOCITY = 0.012      # require downward velocity (ratio/sec) greater than this
TILT_CONSEC_FRAMES = 10    # sustained frames to trigger head-tilt alert

# ---------------------------------------------------------

# Mediapipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.5)

cap = cv2.VideoCapture(0)
time.sleep(0.5)

# deques for smoothing
ear_buf = collections.deque(maxlen=EAR_SMOOTH_WINDOW)
mar_buf = collections.deque(maxlen=MAR_SMOOTH_WINDOW)
tilt_buf = collections.deque(maxlen=TILT_SMOOTH_WINDOW)
tilt_time_buf = collections.deque(maxlen=TILT_SMOOTH_WINDOW)

# counters
ear_close_counter = 0
mar_counter = 0
tilt_counter = 0

# calibration values
EAR_THRESH = None
TILT_BASELINE = None

def notify_server(ev_type):
    try:
        requests.post(SERVER_URL, json={"drowsy": True, "type": ev_type}, timeout=0.6)
    except Exception:
        pass

# ---------------- Calibration ----------------
print("Calibration: Keep your head straight and eyes fully open for a few seconds...")
cal_ear_sum = 0.0
cal_tilt_sum = 0.0
cal_count = 0
for i in range(CALIBRATION_FRAMES):
    ret, frame = cap.read()
    if not ret:
        continue
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = face_mesh.process(rgb)
    if res.multi_face_landmarks:
        lm = res.multi_face_landmarks[0].landmark
        try:
            cal_ear_sum += calculate_ear(lm, w, h)
            cal_tilt_sum += head_nose_eye_ratio(lm, w, h)
            cal_count += 1
        except Exception:
            continue

if cal_count == 0:
    print("Calibration failed: no face detected. Using default thresholds.")
    EAR_THRESH = 0.25
    TILT_BASELINE = 0.35
else:
    open_eye_ear = cal_ear_sum / cal_count
    EAR_THRESH = open_eye_ear * EAR_THRESH_FACTOR
    TILT_BASELINE = cal_tilt_sum / cal_count
print(f"Calibration complete — EAR_THRESH={EAR_THRESH:.3f}, TILT_BASELINE={TILT_BASELINE:.3f}")

# --------------- Main loop ------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = face_mesh.process(rgb)

    ear_val = None
    mar_val = None
    tilt_ratio = None

    if res.multi_face_landmarks:
        lm = res.multi_face_landmarks[0].landmark
        # compute measures
        ear_val = calculate_ear(lm, w, h)
        mar_val = calculate_mar(lm, w, h)
        tilt_ratio = head_nose_eye_ratio(lm, w, h)

        # smoothing
        ear_buf.append(ear_val)
        mar_buf.append(mar_val)
        tilt_buf.append(tilt_ratio)
        tilt_time_buf.append(time.time())

        ear_avg = sum(ear_buf) / len(ear_buf)
        mar_avg = sum(mar_buf) / len(mar_buf)
        tilt_avg = sum(tilt_buf) / len(tilt_buf)

        # compute tilt velocity (slope) using last two points if possible
        tilt_velocity = 0.0
        if len(tilt_buf) >= 2:
            # velocity = delta_ratio / delta_time
            dt = tilt_time_buf[-1] - tilt_time_buf[-2]
            if dt > 1e-6:
                tilt_velocity = (tilt_buf[-1] - tilt_buf[-2]) / dt

        # Draw small HUD
        cv2.putText(frame, f"EAR: {ear_avg:.3f}", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.putText(frame, f"MAR: {mar_avg:.3f}", (12, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,255), 2)
        cv2.putText(frame, f"TiltR: {tilt_avg:.3f}", (12, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,200,255), 2)
        cv2.putText(frame, f"TVel: {tilt_velocity:+.4f}", (12, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

        # ----- EYE (drowsiness) check -----
        if ear_avg < EAR_THRESH:
            ear_close_counter += 1
            if ear_close_counter >= EAR_CONSEC_FRAMES:
                cv2.putText(frame, "DROWSINESS ALERT!", (w//6, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)
                play_alarm()
                notify_server("drowsiness")
        else:
            ear_close_counter = 0
            # stop alarm only if nothing else is alerting (simple approach)
            stop_alarm()

        # ----- YAWN check (MAR) -----
        if mar_avg > MAR_THRESH:
            mar_counter += 1
            if mar_counter >= MAR_CONSEC_FRAMES:
                cv2.putText(frame, "YAWN ALERT!", (w//6, h//2 + 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,0,255), 3)
                play_alarm()
                notify_server("yawn")
        else:
            mar_counter = 0

        # ----- HEAD TILT detection (downwards) -----
        # Condition: ratio increase above baseline by TILT_DELTA_RATIO
        # AND tilt velocity is sufficiently negative (nose moving downward -> positive ratio increase => velocity positive)
        # Note: nose_y - eye_center_y increases when head moves down, so velocity > 0 indicates downward motion
        tilt_condition = False
        if tilt_avg is not None:
            delta = tilt_avg - TILT_BASELINE
            if (delta > TILT_DELTA_RATIO) and (tilt_velocity > TILT_VELOCITY):
                tilt_counter += 1
                if tilt_counter >= TILT_CONSEC_FRAMES:
                    tilt_condition = True
            else:
                tilt_counter = 0

        if tilt_condition:
            cv2.putText(frame, "HEAD TILT ALERT!", (w//6, h//2 + 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,140,255), 3)
            play_alarm()
            notify_server("head_tilt")

    # controls text and display
    cv2.putText(frame, "Press 'r' to recalibrate | 'q' to quit", (10, frame.shape[0]-20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)

    cv2.imshow("Drowsiness Detection (Stable)", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    if key == ord('r'):
        # quick recalibration (same as startup)
        print("Recalibrating... keep head straight and eyes open.")
        cal_sum_ear = 0.0
        cal_sum_tilt = 0.0
        cal_count = 0
        for i in range(CALIBRATION_FRAMES):
            ret, f2 = cap.read()
            if not ret: continue
            hh, ww, _ = f2.shape
            rgb2 = cv2.cvtColor(f2, cv2.COLOR_BGR2RGB)
            r2 = face_mesh.process(rgb2)
            if r2.multi_face_landmarks:
                lm2 = r2.multi_face_landmarks[0].landmark
                try:
                    cal_sum_ear += calculate_ear(lm2, ww, hh)
                    cal_sum_tilt += head_nose_eye_ratio(lm2, ww, hh)
                    cal_count += 1
                except Exception:
                    pass
        if cal_count > 0:
            open_eye_ear = cal_sum_ear / cal_count
            EAR_THRESH = open_eye_ear * EAR_THRESH_FACTOR
            TILT_BASELINE = cal_sum_tilt / cal_count
            print(f"Recal complete — EAR_THRESH={EAR_THRESH:.3f}, TILT_BASELINE={TILT_BASELINE:.3f}")
        else:
            print("Recalibration failed (no face).")

cap.release()
cv2.destroyAllWindows()
