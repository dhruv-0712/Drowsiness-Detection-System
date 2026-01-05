# Drowsiness-Detection-System
A real-time driver drowsiness detection system using CNN-based facial landmark detection (Mediapipe). It monitors eye closure, yawning, and head tilt, triggers audio alerts, updates a live dashboard, and sends SMS notifications during repeated drowsiness to improve road safety.
# 🚗 Driver Drowsiness Detection & Alert System

A real-time driver drowsiness detection system that uses a CNN-based facial landmark model to monitor eye closure, yawning, and head tilt. The system provides instant alerts, a live web dashboard, and SMS notifications to help prevent accidents caused by driver fatigue.

---

## 🔍 Overview

This project continuously monitors a driver through a webcam and detects signs of drowsiness using facial features. A deep learning-based **Mediapipe Face Mesh (CNN)** model extracts facial landmarks, which are used to calculate:

- Eye Aspect Ratio (EAR) – eye closure detection  
- Mouth Aspect Ratio (MAR) – yawning detection  
- Head Tilt (Pitch) – microsleep indication  

Alerts are generated locally and sent to a backend server for visualization and SMS notification.

---

## ✨ Features

- Real-time webcam-based monitoring  
- CNN-based facial landmark detection  
- Eye closure (EAR) detection  
- Yawning (MAR) detection  
- Downward head tilt detection  
- Driver-only face tracking  
- Audio alarm alerts  
- Live web dashboard (real-time updates)  
- SMS notification for repeated drowsiness (Twilio)  
- Adaptive eye calibration for accuracy  

---

## 🧠 Machine Learning Used

- **Mediapipe Face Mesh**
  - CNN-based deep learning model
  - Predicts 468 facial landmarks in real time

> EAR, MAR, and head pose calculations are mathematical algorithms applied on the ML model output.

---

## 🛠️ Tech Stack

**Languages & Libraries**
- Python
- OpenCV
- Mediapipe
- NumPy
- Pygame

**Backend & Dashboard**
- Flask
- Flask-SocketIO
- HTML, CSS, JavaScript
- Chart.js

**Notifications**
- Twilio SMS API

---

## 📁 Project Structure

renewed project/
│
├── main.py
├── algorithm.py
├── alerts.py
│
└── server/
├── app.py
├── notifier.py
├── templates/
│ └── index.html
└── .env

yaml
Copy code

---

## 🚀 How to Run

### 1️⃣ Start the backend server
```bash
cd server
python app.py
2️⃣ Run the detection system
bash
Copy code
python main.py
3️⃣ Open the dashboard
cpp
Copy code
http://127.0.0.1:5000
📩 SMS Notification Setup
Add your Twilio credentials in server/.env:

ini
Copy code
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
NOTIFY_PHONES=+91XXXXXXXXXX
NOTIFICATION_COOLDOWN_SEC=600
SMS is sent only when drowsiness is detected multiple times within a time window.

📌 Use Cases
Driver fatigue monitoring

Road safety systems

Fleet management

Smart vehicle safety solutions

Academic and research projects

🔮 Future Enhancements
Mobile app integration

Cloud database for long-term analytics

Multiple driver profiles

GPS-based emergency alerts

🤝 Contribution
Contributions and improvements are welcome.
Feel free to fork this repository or raise an issue.

📜 License
This project is for educational and research purposes.


