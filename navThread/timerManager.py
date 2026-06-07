from typing import Callable 

class TimerManager:
    def __init__(self, node: Node):
        self.node = node
        self.active_timers: dict[str, RosTimer] = {}

    def start_timer(
        self,
        name: str,
        delay_seconds: float,
        callback: Callable[[], None]
    ) -> None:

        self.cancel_timer(name)

        def timer_wrapper():
            self.cancel_timer(name)
            callback()

        self.active_timers[name] = self.create_timer(
            delay_seconds,
            timer_wrapper
        )

    def cancel_timer(self, name: str):
        timer = self.active_timers.pop(name, None)

        if timer is not None:
            timer.cancel()

    def cancel_all_timers(self):
        for timer in self.active_timers.values():
            timer.cancel()

        self.active_timers.clear()