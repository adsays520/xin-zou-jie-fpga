import threading
import time


class SerializedPort:
    def __init__(self, port):
        object.__setattr__(self, '_port', port)
        object.__setattr__(self, '_write_lock', threading.RLock())

    @classmethod
    def wrap(cls, port):
        return port if isinstance(port, cls) else cls(port)

    def __getattr__(self, name):
        return getattr(self._port, name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._port, name, value)

    def write(self, data):
        with self._write_lock:
            return self._port.write(data)

    def write_bounded(self, data, timeout=0.1):
        if not self._write_lock.acquire(timeout=timeout):
            raise TimeoutError(f'串口被其他任务占用超过{timeout * 1000:.0f}ms')
        try:
            configurable = hasattr(self._port, 'write_timeout')
            previous = getattr(self._port, 'write_timeout', None)
            try:
                if configurable:
                    self._port.write_timeout = timeout if previous is None else min(previous, timeout)
                started = time.monotonic()
                written = self._port.write(data)
                elapsed = time.monotonic() - started
                if written != len(data):
                    raise IOError(f'串口部分写入：{written}/{len(data)}字节')
                if elapsed > timeout:
                    raise TimeoutError(f'串口写入耗时{elapsed * 1000:.1f}ms，超过{timeout * 1000:.0f}ms')
                return written
            finally:
                if configurable:
                    self._port.write_timeout = previous
        finally:
            self._write_lock.release()

    def flush(self):
        with self._write_lock:
            return self._port.flush()

    def close(self):
        with self._write_lock:
            return self._port.close()


class PlaybackSender:
    def __init__(self, port, timeout=0.1):
        self.port = SerializedPort.wrap(port)
        self.timeout = timeout
        self.failed = False
        self.error = ''

    def __call__(self, data):
        if self.failed:
            raise IOError(self.error)
        try:
            if not self.port.is_open:
                raise IOError('播放串口已关闭')
            self.port.write_bounded(data, self.timeout)
            return True
        except Exception as error:
            self.failed = True
            self.error = str(error)
            raise
