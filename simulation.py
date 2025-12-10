import threading
import time

from state import system_state


def start_load_decay_worker(decay_step: float = 1.0, interval: float = 1.0) -> None:
    """
    Start a background thread that periodically calls system_state.decay_load().

    - decay_step: how much 'work' to remove from each center per tick
    - interval: how often to tick, in seconds

    Example: if expected_duration is like 'minutes', then
             decay_step = 1.0 every 1 second means
             1 'minute' of simulated work completes per real second.
    """

    def worker() -> None:
        while True:
            system_state.decay_load(decay_step=decay_step)
            time.sleep(interval)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
