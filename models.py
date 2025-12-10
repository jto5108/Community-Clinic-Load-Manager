from dataclasses import dataclass, field
from threading import Lock
from typing import List, Optional
import time

from pydantic import BaseModel


# ---------- Domain models (in-memory) ----------

@dataclass
class Center:
    id: int
    name: str
    capacity: int  # how many "time units" it can handle in parallel
    current_load: float = 0.0  # total remaining work (approx)
    is_up: bool = True
    lock: Lock = field(default_factory=Lock, repr=False)

    def predicted_wait_time(self, extra_work: float = 0.0) -> float:
        """
        Very simple SJF-style predictor:
        approximate waiting time by (current_load + new_work) / capacity.
        """
        if not self.is_up or self.capacity <= 0:
            return float("inf")
        return (self.current_load + extra_work) / self.capacity


@dataclass
class AppointmentRequest:
    id: int
    urgency: int  # smaller = higher priority
    expected_duration: float
    arrival_time: float
    assigned_center_id: Optional[int] = None


@dataclass
class RoutingEvent:
    timestamp: float
    request_id: int
    center_id: int
    reason: str


# ---------- Pydantic models for API ----------

class CenterCreate(BaseModel):
    name: str
    capacity: int


class CenterOut(BaseModel):
    id: int
    name: str
    capacity: int
    current_load: float
    is_up: bool

    class Config:
        from_attributes = True


class AppointmentIn(BaseModel):
    urgency: int = 5          # e.g., 1 = crisis, 10 = routine
    expected_duration: float  # in "time units" (e.g., 30.0 minutes)


class AppointmentOut(BaseModel):
    id: int
    center_id: int
    center_name: str
    predicted_wait_time: float
    urgency: int
    expected_duration: float


class RoutingEventOut(BaseModel):
    timestamp: float
    request_id: int
    center_id: int
    reason: str
