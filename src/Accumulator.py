import logging
import time


class Accumulator:
    FLUSH_INTERVAL = 20

    def __init__(self, external_function):
        self.data = []
        self.external_function = external_function
        self.start_time = time.time()
        self.next_flush_time = self.start_time + self.FLUSH_INTERVAL

    def add(self, item):
        current_time = time.time()
        if current_time >= self.next_flush_time:
            self.flush()
            self.start_time = current_time
            self.next_flush_time = self.start_time + self.FLUSH_INTERVAL
        else:
            self.data.append(item)

    def flush(self):
        end = time.time()
        flush_duration = end - self.start_time
        self.external_function(self.data)
        logging.info(
            '\n' +
            f'Data flushed. Items added {self.len()}. Flush time: {round(flush_duration, 2)}. Avg speed: {round(self.len() / flush_duration, 2)} items/s' +
            '\n'
        )
        self.data.clear()

    def len(self) -> int:
        return len(self.data) + 1
