from typing import Dict, List
import time

from models import Center, AppointmentRequest, RoutingEvent


class SystemState:
    def __init__(self) -> None:
        self.centers: Dict[int, Center] = {}
        self.requests: Dict[int, AppointmentRequest] = {}
        self.history: List[RoutingEvent] = []
        self._next_center_id = 1
        self._next_request_id = 1

    def add_center(self, name: str, capacity: int) -> Center:
        cid = self._next_center_id
        self._next_center_id += 1
        center = Center(id=cid, name=name, capacity=capacity)
        self.centers[cid] = center
        return center

    def create_request(self, urgency: int, expected_duration: float) -> AppointmentRequest:
        rid = self._next_request_id
        self._next_request_id += 1
        req = AppointmentRequest(
            id=rid,
            urgency=urgency,
            expected_duration=expected_duration,
            arrival_time=time.time(),
        )
        self.requests[rid] = req
        return req

    def add_event(self, event: RoutingEvent) -> None:
        self.history.append(event)

    def decay_load(self, decay_step: float = 1.0) -> None:
        for center in self.centers.values():
            with center.lock:
                if center.current_load > 0:
                    effective_step = decay_step * center.capacity / 10
                    center.current_load = max(0.0, center.current_load - effective_step)



# A single global state instance for the whole app (like the OS's process table)
system_state = SystemState()
