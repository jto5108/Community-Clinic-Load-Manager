from typing import Optional
import time

from models import AppointmentRequest, RoutingEvent, Center
from state import system_state


def choose_best_center(request: AppointmentRequest) -> Optional[Center]:
    """
    SJF / least-loaded routing:
    - Among all "up" centers, choose one with minimum predicted wait time.
    - predicted_wait = (current_load + new_work) / capacity
    """
    candidates = [c for c in system_state.centers.values() if c.is_up and c.capacity > 0]
    if not candidates:
        return None

    # SJF-inspired: choose center with min predicted completion time
    best = min(
        candidates,
        key=lambda c: (c.predicted_wait_time(request.expected_duration), request.urgency),
    )
    return best


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
