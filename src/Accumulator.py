import logging
import time


class Accumulator:
    MAX_FLUSH_INTERVAL = 40
    MIN_FLUSH_INTERVAL = 10

    def __init__(self, external_function):
        self.item_limit = 100
        self.data = []
        self.total_items_added = 0
        self.external_function = external_function
        self.start_time = time.time()
        self.flush_interval = self.MIN_FLUSH_INTERVAL
        self.next_flush_time = self.start_time + self.flush_interval

    def update_flush_interval(self):
        if len(self.data) > 0.8 * self.item_limit:
            new_interval = max(self.MIN_FLUSH_INTERVAL, self.flush_interval - 1)
            if new_interval != self.flush_interval:
                logging.info(f'Flush interval updated from {self.flush_interval}s to {new_interval}s')
                self.flush_interval = new_interval
        elif len(self.data) < 0.5 * self.item_limit:
            new_interval = min(self.MAX_FLUSH_INTERVAL, self.flush_interval + 1)
            if new_interval != self.flush_interval:
                logging.info(f'Flush interval updated from {self.flush_interval}s to {new_interval}s')
                self.flush_interval = new_interval

    def add(self, item):
        current_time = time.time()
        if current_time >= self.next_flush_time or len(self.data) >= self.item_limit:
            self.flush()
            self.start_time = current_time
            self.update_flush_interval()
            self.next_flush_time = self.start_time + self.flush_interval  # Update the next flush time
        else:
            self.data.append(item)
            self.total_items_added += 1

    def flush(self):
        self.external_function(self.data)
        logging.info(
            f'Data flushed. Items added {self.total_items_added}. Avg speed: {round(self.total_items_added / self.flush_interval, 2)} items/s')
        self.data.clear()
        self.total_items_added = 0

    def get_len(self):
        return len(self.data)
