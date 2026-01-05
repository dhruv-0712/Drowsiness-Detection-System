# algorithm.py
import numpy as np

def _pt(landmarks, idx, w, h):
    p = landmarks[idx]
    return np.array([p.x * w, p.y * h])

def calculate_ear(landmarks, w, h):
    """
    Eye Aspect Ratio using a few reliable FaceMesh indices.
    Returns a single float EAR.
    """
    # left eye indices (mediapipe face mesh)
    # we use a conservative subset for robustness
    try:
        p0 = _pt(landmarks, 33, w, h)   # left corner
        p1 = _pt(landmarks, 160, w, h)  # upper inner
        p2 = _pt(landmarks, 158, w, h)  # upper inner 2
        p3 = _pt(landmarks, 133, w, h)  # right corner
        p4 = _pt(landmarks, 153, w, h)  # lower inner
        p5 = _pt(landmarks, 144, w, h)  # lower inner 2

        A = np.linalg.norm(p1 - p5)
        B = np.linalg.norm(p2 - p4)
        C = np.linalg.norm(p0 - p3)
        ear = (A + B) / (2.0 * C + 1e-8)
        return float(ear)
    except Exception:
        return 0.0


def calculate_mar(landmarks, w, h):
    """
    Mouth Aspect Ratio. We average two vertical measures to be more robust.
    Returns MAR float.
    """
    try:
        # Use inner mouth vertical (13, 14) and another vertical pair (78, 308) if present
        top1 = _pt(landmarks, 13, w, h)
        bot1 = _pt(landmarks, 14, w, h)
        top2 = _pt(landmarks, 78, w, h)
        bot2 = _pt(landmarks, 308, w, h)

        left = _pt(landmarks, 61, w, h)
        right = _pt(landmarks, 291, w, h)

        vert1 = np.linalg.norm(top1 - bot1)
        vert2 = np.linalg.norm(top2 - bot2)
        horiz = np.linalg.norm(left - right) + 1e-8

        mar = (vert1 + vert2) / (2.0 * horiz)
        return float(mar)
    except Exception:
        # fallback to a simple vertical pair
        try:
            top = _pt(landmarks, 13, w, h)
            bot = _pt(landmarks, 14, w, h)
            left = _pt(landmarks, 61, w, h)
            right = _pt(landmarks, 291, w, h)
            mar = np.linalg.norm(top - bot) / (np.linalg.norm(left - right) + 1e-8)
            return float(mar)
        except Exception:
            return 0.0


def head_nose_eye_ratio(landmarks, w, h):
    """
    Return a normalized vertical ratio (nose_y - eye_center_y) / face_height.
    This ratio scales with face size and is good for baseline + delta checks.
    """
    try:
        nose = _pt(landmarks, 1, w, h)      # nose tip
        left_eye = _pt(landmarks, 33, w, h)
        right_eye = _pt(landmarks, 263, w, h)
        chin = _pt(landmarks, 152, w, h)

        eye_center_y = (left_eye[1] + right_eye[1]) / 2.0
        face_height = np.abs(chin[1] - eye_center_y) + 1e-8

        ratio = (nose[1] - eye_center_y) / face_height
        return float(ratio)
    except Exception:
        return 0.0
