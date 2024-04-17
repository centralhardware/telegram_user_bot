import logging
import time

from termcolor import colored


class Accumulator:
    FLUSH_INTERVAL = 20

    def __init__(self, external_function):
        self.item_limit = 100
        self.data = []
        self.total_items_added = 0
        self.external_function = external_function
        self.start_time = time.time()
        self.flush_interval = self.FLUSH_INTERVAL
        self.next_flush_time = self.start_time + self.flush_interval

    def add(self, item):
        current_time = time.time()
        if current_time >= self.next_flush_time:
            self.flush(is_time_up=True)
            self.start_time = current_time
            self.next_flush_time = self.start_time + self.flush_interval
        elif len(self.data) >= self.item_limit:
            self.flush(is_time_up=False)
        else:
            self.data.append(item)
            self.total_items_added += 1

    def flush(self, is_time_up):
        end = time.time()
        flush_duration = round(end - self.start_time, 2)
        speed = round(self.total_items_added / flush_duration, 2)
        logging.info(colored(
            f'Data flushed due to {"time up" if is_time_up else "limit reached"}. Items added: {self.total_items_added}. Flush time: {flush_duration}. Avg speed: {speed} items/s',
            'blue' if is_time_up else 'green'))


        self.data.clear()
        self.total_items_added = 0

    def get_len(self):
        return len(self.data)
