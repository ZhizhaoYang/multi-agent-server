from enum import Enum


class SupervisorStatus(str, Enum):
    IDLE = "idle"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"