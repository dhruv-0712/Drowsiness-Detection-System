# server/app.py
import os
import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from notifier import send_notification

load_dotenv()  # loads server/.env if present

app = Flask(__name__, template_folder="templates", static_folder="static")
socketio = SocketIO(app, cors_allowed_origins="*")

# Notification policy (configurable via env)
NOTIFY_WINDOW_SEC = int(os.getenv("NOTIFY_WINDOW_SEC", 60 * 30))  # default 30 minutes
NOTIFY_THRESHOLD = int(os.getenv("NOTIFY_THRESHOLD", 2))         # default 2 events to escalate

# In-memory event list (timestamp, type) — for simple runs. Replace with DB for persistence.
events = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/update", methods=["POST"])
def update():
    """
    Endpoint that detector posts to:
      POST /update   JSON payload example: {"drowsy": true, "type": "drowsiness"}
    """
    data = request.get_json() or {}
    ev_type = data.get("type", "drowsiness" if data.get("drowsy") else "unknown")
    ts = datetime.datetime.utcnow()
    events.append((ts, ev_type))

    # emit event to connected web clients (dashboard)
    try:
        socketio.emit("new_event", {"ts": ts.isoformat(), "type": ev_type})
    except Exception:
        pass

    # count events in the window
    window_start = ts - datetime.timedelta(seconds=NOTIFY_WINDOW_SEC)
    recent = [e for e in events if e[0] >= window_start]
    count = len(recent)

    # If threshold reached, notify and remove those recent events to avoid repeat notifications
    if count >= NOTIFY_THRESHOLD:
        print(f"[ALERT] {count} events in last {NOTIFY_WINDOW_SEC} seconds. Triggering notification.")
        notify_result = send_notification(count)
        # clean up recent events so next notification waits for new ones
        events[:] = [e for e in events if e[0] < window_start]
        return jsonify({"ok": True, "notified": True, "result": notify_result})

    return jsonify({"ok": True, "notified": False, "current_count": count})

@app.route("/events", methods=["GET"])
def get_events():
    # return recent events (simple)
    rows = [{"ts": e[0].isoformat(), "type": e[1]} for e in events]
    return jsonify(rows)

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=PORT)
