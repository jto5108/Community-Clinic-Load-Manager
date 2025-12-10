from typing import Optional
import time

from models import AppointmentRequest, RoutingEvent, Center
from state import system_state

URGENCY_WEIGHT = 0.2  # higher = urgency matters more

def choose_best_center(request: AppointmentRequest) -> Optional[Center]:
    """
    Choose the best clinic using a combination of:
    - SJF-style predicted wait time
    - urgency-based priority

    score = predicted_wait - urgency * URGENCY_WEIGHT

    Lower score = better.
    """
    candidates = [c for c in system_state.centers.values() if c.is_up and c.capacity > 0]
    if not candidates:
        return None

    best_center: Optional[Center] = None
    best_score: float = float("inf")

    for center in candidates:
        predicted_wait = center.predicted_wait_time(request.expected_duration)
        score = predicted_wait - (request.urgency * URGENCY_WEIGHT)

        if score < best_score:
            best_score = score
            best_center = center

    return best_center



def route_request(request: AppointmentRequest) -> Optional[Center]:
    """
    Critical section: updating center.current_load must be protected by a lock
    to avoid race conditions when multiple requests come in concurrently.
    """
    center = choose_best_center(request)
    if center is None:
        return None

    # ---- Critical Section (protected by mutex) ----
    with center.lock:
        # Entry section (mutex acquired)
        center.current_load += request.expected_duration
        # Critical section: update shared state

    # Exit section: lock automatically released by context manager
    request.assigned_center_id = center.id
    system_state.add_event(
        RoutingEvent(
            timestamp=time.time(),
            request_id=request.id,
            center_id=center.id,
            reason="least_loaded_sjf",
        )
    )
    return center
