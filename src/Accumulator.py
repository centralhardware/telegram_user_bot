import logging
import time


class Accumulator:
    FLUSH_INTERVAL = 20

    def __init__(self, external_function):
        self.item_limit = 50  # Updated item limit to 50
        self.data = []
        self.total_items_added = 0
        self.external_function = external_function
        self.start_time = time.time()
        self.flush_interval = self.FLUSH_INTERVAL
        self.next_flush_time = self.start_time + self.flush_interval

    def add(self, item):
        current_time = time.time()
        if current_time >= self.next_flush_time or len(self.data) >= self.item_limit:
            self.flush()
            self.start_time = current_time
            self.next_flush_time = self.start_time + self.flush_interval  # Update the next flush time
        else:
            self.data.append(item)
            self.total_items_added += 1

    def flush(self):
        end = time.time()
        self.external_function(self.data)
        logging.info(
            f'Data flushed. Items added {self.total_items_added}. Avg speed: {round(self.total_items_added / (end - self.start_time), 2)} items/s')
        self.data.clear()
        self.total_items_added = 0

    def get_len(self):
        return len(self.data)
