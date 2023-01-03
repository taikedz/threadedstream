from threading import Thread, RLock, Event
import time

from threadedstream.errors import StoppedThreadError
from threadedstream.NonBlockingStream import NonBlockingStream

class ThreadedStream(Thread):
    """ Class whose role is to provide thread safety on input and output buffers.

    This class MUST be subclassed with non-blocking implementations of the
     _raw_read and _raw_write methods for underlying actual transport streams.

    Instances are context-managed, for use in `with ...` blocks.
    """
    def __init__(self, tick):
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
        self._raw_close()


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
                received = self._raw_read()
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
                written = self._raw_write(self._out_buffer)
                self._out_buffer = self._out_buffer[written:]
            except Exception as e:
                self._stored_error = e
                self._alive = False


    def __enter__(self):
        self.start()
        return self


    def __exit__(self, *e):
        pass

    # Subclasses MUST implement the following two methods.

    def _raw_read(self, count:int=4096) -> Union[str,bytes]:
        """ Subclasses MUST implement this method.

        Implementation:

        - must not block when reading
        - should return at most `count` number of bytes
        - must not call ths superclass method
        """
        raise NotImplementedError("Override this method. Do not call it.")


    def _raw_write(self, data:Union[str,bytes]) -> int:
        """ Subclasses MUST implement this method.

        Implementation:

        - must not block to write
        - must return the number of bytes successfully written
        - must not call ths superclass method
        """
        raise NotImplementedError("Override this method. Do not call it.")


    def _raw_close(self):
        """ Subclasses are recommended to implement this method, to close their underlying stream.
        """
        pass
