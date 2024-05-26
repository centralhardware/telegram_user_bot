import logging
import time


class Accumulator:
    def __init__(self, external_function, name):
        self.name = name
        self.data = []
        self.external_function = external_function
        self.start_time = time.time()

    def add(self, item):
        current_time = time.time()
        if len(self.data) == 10:
            self.flush()
            self.start_time = current_time
        else:
            self.data.append(item)

    def flush(self):
        end = time.time()
        flush_duration = end - self.start_time
        self.external_function(self.data)
        logging.info(
            '\n' +
            f'{self.name} flushed. Items added {self.len()}. Flush time: {round(flush_duration, 2)}. Avg speed: {round(self.len() / flush_duration, 2)} items/s' +
            '\n'
        )
        self.data.clear()

    def len(self) -> int:
        return len(self.data) + 1
