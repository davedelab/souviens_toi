### memex_next/services/async_worker.py
import queue, threading

class TaskRunner:
    def __init__(self):
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def submit(self, fn, cb=None):
        self.q.put((fn, cb))

    def _run(self):
        while True:
            fn, cb = self.q.get()
            res = err = None
            try:
                res = fn()
            except Exception as e:
                err = e
            if cb:
                try:
                    cb(res, err)
                except Exception:
                    pass

runner = TaskRunner()
