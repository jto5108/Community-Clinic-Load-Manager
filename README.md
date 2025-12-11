# Community Clinic Load Manager
Our mission is to improve timely access to mental-health support by intelligently routing users to available resources, ensuring fairness, reduced wait times, and reliable assistance through OS-based system design.

Features

Live dashboard showing clinic load, utilization, and routing history
SJF-inspired load balancing for appointment requests
Urgency-aware scheduling
Background load decay thread that simulates appointments finishing
Thread-safe shared state using mutex locks
FastAPI backend with automatic /docs API UI


Project Structure
clinic_load_manager/
│   main.py          # FastAPI app + routes
│   models.py        # Data models
│   scheduler.py     # Routing logic
│   simulation.py    # Load decay worker
│   state.py         # Shared system state
│   requirements.txt


How to Run
pip install -r requirements.txt
uvicorn main:app --reload


Dashboard: http://127.0.0.1:8000/dashboard

API Docs: http://127.0.0.1:8000/docs
