import time


class Accumulator:
    def __init__(self, item_limit, external_function):
        self.item_limit = max(item_limit, 50)
        self.data = []
        self.total_items_added = 0
        self.external_function = external_function
        self.start_time = time.time()
        self.last_flush_time = 0

    def add(self, item):
        if len(self.data) < self.item_limit:
            self.data.append(item)
            self.total_items_added += 1
        else:
            self.flush()
            self.start_time = time.time()

    def flush(self):
        self.external_function(self.data)
        flush_time = time.time() - self.start_time
        adjustment = int(self.item_limit * 0.1)
        if self.last_flush_time:
            if flush_time < self.last_flush_time:
                self.item_limit += adjustment
                print(f'Resizing the item limit. New limit: {self.item_limit}')
            elif flush_time > self.last_flush_time:
                self.item_limit = max(50, self.item_limit - adjustment)
                print(f'Resizing the item limit. New limit: {self.item_limit}')
        self.last_flush_time = flush_time
        print(
            f'Data flushed. Time taken: {flush_time}s. New item limit: {self.item_limit}. Avg speed: {(end - self.start_time) / (self.total_items_added if self.total_items_added > 0 else 1)} items/s')
        self.data.clear()

    def get_len(self):
        return len(self.data)