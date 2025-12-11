from typing import Optional, Tuple
import time

from models import AppointmentRequest, RoutingEvent, Center
from state import system_state


def choose_best_center(request: AppointmentRequest) -> Tuple[Optional[Center], str]:
    """
    Hybrid scheduling:
    - For low/medium urgency (1–5): pure SJF based on predicted_wait.
    - For high urgency (6–10): priority override to the highest-capacity clinic.

    We still compute the SJF choice first so we can log whether
    we overrode it or not.
    """
    candidates = [c for c in system_state.centers.values() if c.is_up and c.capacity > 0]
    if not candidates:
        return None, "no_centers"

    # --- 1) Pure SJF choice ---
    def sjf_wait(center: Center) -> float:
        # Uses your existing predicted_wait_time helper
        return center.predicted_wait_time(request.expected_duration)

    sjf_center = min(candidates, key=sjf_wait)

    # --- 2) If urgency is low (1–5), just use SJF ---
    if request.urgency <= 5:
        return sjf_center, "least_loaded_sjf"

    # --- 3) If urgency is high (6–10), prefer the highest-capacity clinic ---
    # (like sending emergencies to the largest hospital)
    priority_center = max(candidates, key=lambda c: c.capacity)

    if priority_center.id != sjf_center.id:
        # We truly overrode the SJF decision
        return priority_center, "priority_override"
    else:
        # Even with priority, SJF and priority agree
        return sjf_center, "least_loaded_sjf"


def route_request(request: AppointmentRequest) -> Optional[Center]:
    """
    Critical section: updating center.current_load must be protected by a lock
    to avoid race conditions when multiple requests come in concurrently.
    """
    center, reason = choose_best_center(request)
    if center is None:
        return None

    # ---- Critical Section (protected by mutex) ----
    with center.lock:
        center.current_load += request.expected_duration

    request.assigned_center_id = center.id
    system_state.add_event(
        RoutingEvent(
            timestamp=time.time(),
            request_id=request.id,
            center_id=center.id,
            reason=reason,
        )
    )
    return center
