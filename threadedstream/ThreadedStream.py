from threading import Thread, RLock, Event
import time

from threadedstream.errors import StoppedThreadError
from threadedstream.NonBlockingStream import NonBlockingStream

class ThreadedStream(Thread):
    """ Class whose role is to provide thread safety on input and output buffers.

    It must receive a non-blocking NonBlockingStream implementation that provides read_bytes() and write_bytes()
    methods.

    Instances are context-managed, for use in `with ...` blocks.
    """
    def __init__(self, _nonb_stream_stream:NonBlockingStream, tick=10e9):
        self.__nonb_stream = _nonb_stream_stream

        # Time to wait before attempting to read again.
        # This improves performance by not obsessively consuming CPU cycles unnecessarily
        self._tick = tick

        self._in_buffer = []
        self._in_buffer_lock = RLock()
        self._in_buffer_updated = Event()

        self._out_buffer = []
        self._out_buffer_lock = RLock()
        self._out_buffer_updated = Event()

        self._alive = True
        self._stored_error = None


    def run(self):
        while self._alive:
            self._inner_read()
            self._inner_write()

            time.sleep(self._tick)


    def stop(self):
        self._alive = False
        self._in_buffer_updated.set()
        self._out_buffer_updated.set()
        self._stored_error = StoppedThreadError("Thread was stopped.")
        self.__nonb_stream.close()


    def read(self, count=4096):
        with self._in_buffer_lock:
            if self._stored_error:
                raise self._stored_error
            res = self._in_buffer[:count]
            self._in_buffer = self._in_buffer[count:]
            return res


    def _inner_read(self):
        with self._in_buffer_lock:
            self._in_buffer_updated.clear()
            try:
                received = self.__nonb_stream.read()
                self._in_buffer = self._in_buffer + received
            except Exception as e:
                self._stored_error = e
                self._alive = False

            self._in_buffer_updated.set()


    def write(self, data):
        with self._out_buffer_lock:
            if self._stored_error:
                raise self._stored_error
            self._out_buffer = self._out_buffer + data


    def _inner_write(self):
        with self._out_buffer_lock:
            try:
                written = self.__nonb_stream.write(self._out_buffer)
                self._out_buffer = self._out_buffer[written:]
            except Exception as e:
                self._stored_error = e
                self._alive = False


    def __enter__(self):
        self.start()
        return self


    def __exit__(self, *e):
        pass
