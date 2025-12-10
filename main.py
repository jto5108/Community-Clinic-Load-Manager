from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from typing import List


from models import (
    CenterCreate,
    CenterOut,
    AppointmentIn,
    AppointmentOut,
    RoutingEventOut,
)
from state import system_state
from scheduler import route_request
from simulation import start_load_decay_worker


app = FastAPI(
    title="Community Clinic Load Manager",
    description=(
        "Simulates community clinics as nodes and intelligently routes "
        "appointment requests to the least-loaded center using OS scheduling "
        "concepts such as SJF, priority scheduling, and synchronization."
    ),
)

@app.on_event("startup")
def startup_event() -> None:
    # Every 1 second, subtract 1.0 time unit from each center's load
    start_load_decay_worker(decay_step=1.0, interval=1.0)

@app.post("/centers", response_model=CenterOut)
def create_center(center_in: CenterCreate):
    center = system_state.add_center(center_in.name, center_in.capacity)
    return center


@app.get("/centers", response_model=List[CenterOut])
def list_centers():
    return list(system_state.centers.values())


@app.post("/appointments", response_model=AppointmentOut)
def request_appointment(app_in: AppointmentIn):
    req = system_state.create_request(
        urgency=app_in.urgency,
        expected_duration=app_in.expected_duration,
    )
    center = route_request(req)
    if center is None:
        raise HTTPException(status_code=503, detail="No centers available")

    predicted_wait = center.predicted_wait_time()  # after adding this request

    return AppointmentOut(
        id=req.id,
        center_id=center.id,
        center_name=center.name,
        predicted_wait_time=predicted_wait,
        urgency=req.urgency,
        expected_duration=req.expected_duration,
    )


@app.get("/history", response_model=List[RoutingEventOut])
def routing_history():
    return [
        RoutingEventOut(
            timestamp=e.timestamp,
            request_id=e.request_id,
            center_id=e.center_id,
            reason=e.reason,
        )
        for e in system_state.history
    ]

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    # Simple HTML + JS dashboard
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Mental Health Load Balancer – Dashboard</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      margin: 0;
      padding: 0;
    }
    header {
      padding: 16px 24px;
      background: #020617;
      border-bottom: 1px solid #1e293b;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    h1 {
      font-size: 20px;
      margin: 0;
    }
    main {
      padding: 16px 24px 32px;
      display: grid;
      grid-template-columns: 2fr 1.2fr;
      gap: 24px;
    }
    section {
      background: #020617;
      border-radius: 12px;
      padding: 16px 18px 18px;
      border: 1px solid #1e293b;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    section h2 {
      margin: 0 0 12px;
      font-size: 16px;
      color: #e5e7eb;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      padding: 6px 8px;
      text-align: left;
    }
    th {
      border-bottom: 1px solid #1f2937;
      font-weight: 600;
      color: #9ca3af;
    }
    tr:nth-child(even) td {
      background: #020617;
    }
    tr:nth-child(odd) td {
      background: #030712;
    }
    .badge-up {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      background: #14532d;
      color: #bbf7d0;
      font-size: 11px;
    }
    .badge-down {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      background: #7f1d1d;
      color: #fecaca;
      font-size: 11px;
    }
    .bar-container {
      background: #020617;
      border-radius: 999px;
      width: 100%;
      height: 9px;
      overflow: hidden;
      border: 1px solid #111827;
    }
    .bar-fill {
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, #22c55e, #eab308, #ef4444);
      width: 0%;
      transition: width 0.4s ease;
    }
    .history-list {
      list-style: none;
      padding: 0;
      margin: 0;
      max-height: 380px;
      overflow-y: auto;
      font-size: 13px;
    }
    .history-item {
      border-bottom: 1px solid #111827;
      padding: 6px 2px;
    }
    .history-item:last-child {
      border-bottom: none;
    }
    .timestamp {
      color: #6b7280;
      font-size: 11px;
    }
    .tag {
      display: inline-block;
      padding: 1px 6px;
      border-radius: 999px;
      background: #1d4ed8;
      color: #dbeafe;
      font-size: 10px;
      margin-left: 6px;
    }
    .controls {
      display: flex;
      gap: 8px;
      align-items: center;
      font-size: 13px;
    }
    .btn {
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid #1d4ed8;
      background: #1d4ed8;
      color: #e5e7eb;
      cursor: pointer;
      font-size: 12px;
    }
    .btn:hover {
      background: #2563eb;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #22c55e;
      display: inline-block;
      margin-right: 6px;
      box-shadow: 0 0 8px rgba(34,197,94,0.9);
    }
    .subtitle {
      font-size: 12px;
      color: #9ca3af;
      margin-top: 4px;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Community Clinic Load Manager – Live Dashboard</h1>
      <div class="subtitle">Simulating OS scheduling for community mental health centers</div>
    </div>
    <div class="controls">
      <span><span class="status-dot"></span>Backend running</span>
      <button class="btn" onclick="manualRefresh()">Refresh now</button>
    </div>
  </header>
  <main>
    <section>
      <h2>Centers & Load</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Center</th>
            <th>Capacity</th>
            <th>Load</th>
            <th>Utilization</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="centers-body">
          <tr><td colspan="6">Loading centers...</td></tr>
        </tbody>
      </table>
    </section>
    <section>
      <h2>Routing History</h2>
      <ul id="history-list" class="history-list">
        <li class="history-item">Waiting for events...</li>
      </ul>
    </section>
  </main>

  <script>
    async function fetchCenters() {
      try {
        const res = await fetch("/centers");
        const centers = await res.json();
        const tbody = document.getElementById("centers-body");
        if (!centers.length) {
          tbody.innerHTML = "<tr><td colspan='6'>No centers configured yet. Use /docs to add some.</td></tr>";
          return;
        }
        let html = "";
        centers.forEach(c => {
          const util = c.capacity > 0 ? Math.min(100, (c.current_load / (c.capacity * 10)) * 100) : 0;
          html += `
            <tr>
              <td>${c.id}</td>
              <td>${c.name}</td>
              <td>${c.capacity}</td>
              <td>${c.current_load.toFixed(1)}</td>
              <td>
                <div class="bar-container">
                  <div class="bar-fill" style="width:${util}%"></div>
                </div>
              </td>
              <td>${c.is_up
                ? "<span class='badge-up'>UP</span>"
                : "<span class='badge-down'>DOWN</span>"}
              </td>
            </tr>
          `;
        });
        tbody.innerHTML = html;
      } catch (err) {
        console.error("Error fetching centers", err);
      }
    }

    function formatTimestamp(ts) {
      const d = new Date(ts * 1000);
      return d.toLocaleTimeString();
    }

    async function fetchHistory() {
      try {
        const res = await fetch("/history");
        const events = await res.json();
        const list = document.getElementById("history-list");
        if (!events.length) {
          list.innerHTML = "<li class='history-item'>No routing events yet. Submit appointments via /docs.</li>";
          return;
        }
        let html = "";
        // Show most recent first
        events.slice().reverse().forEach(e => {
          html += `
            <li class="history-item">
              <div>
                Request <strong>#${e.request_id}</strong> → Center <strong>#${e.center_id}</strong>
                <span class="tag">${e.reason}</span>
              </div>
              <div class="timestamp">${formatTimestamp(e.timestamp)}</div>
            </li>
          `;
        });
        list.innerHTML = html;
      } catch (err) {
        console.error("Error fetching history", err);
      }
    }

    function refreshAll() {
      fetchCenters();
      fetchHistory();
    }

    function manualRefresh() {
      refreshAll();
    }

    // Auto-refresh every 2 seconds
    setInterval(refreshAll, 2000);
    // Initial load
    refreshAll();
  </script>
</body>
</html>
    """

