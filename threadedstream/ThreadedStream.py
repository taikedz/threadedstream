from threading import Thread, RLock, Event
from typing import Union
import time

from threadedstream.errors import StoppedThreadError, set_payload

class ThreadedStream(Thread):
    """ Class whose role is to provide thread safety on input and output buffers.

    This class MUST be subclassed with non-blocking implementations of the
     _raw_read and _raw_write methods for underlying actual transport streams.
    Implementing _raw_close to close the underlying transport stream is recommended
     where applicable.

    Instances are context-managed, for use in `with ...` blocks.

    Methods of this class that raise errors will attach a payload to the exception object
     as `exc.error_payload` which will be a tuple of (read buffer, write buffer)
    """

    # Subclasses MUST implement the following two methods.

    def _raw_read(self, count:int=4096) -> Union[str,bytes]:
        """ Subclasses MUST implement this method.

        Implementation:

        - must not block when reading
        - should return at most `count` number of bytes
        - should return None if nothing to return
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

    # ==== / End of subclassing requirements
    # ======================================

    def __init__(self, tick=10e6):
        Thread.__init__(self)
        self.daemon = True
        # Time to wait before attempting to read again.
        # This improves performance by not obsessively consuming CPU cycles unnecessarily
        self._tick = 1.0/tick

        self._in_buffer = ''
        self._in_buffer_lock = RLock()
        self._in_buffer_updated = Event()

        self._out_buffer = ''
        self._out_buffer_lock = RLock()
        self._out_buffer_updated = Event()

        self._alive = True
        self._stored_error = None


    def __enter__(self):
        self.start()
        return self


    def __exit__(self, *e):
        self.stop()


    def run(self):
        try:
            while self._alive:
                self._inner_read()
                self._inner_write()

                time.sleep(self._tick)

        except Exception as e:
            # We're in the child thread. Pass the error on
            #  so that the read/write operations in the main thread
            #  re-raise the error. We do not need to re-raise here.
            self.set_error_payload(e)

        finally:
            self.stop()


    def stop(self):
        self._alive = False
        self._in_buffer_updated.set()
        self._out_buffer_updated.set()
        self._stored_error = StoppedThreadError("Thread was stopped.")
        self._raw_close()


    def set_error_payload(self, e):
        with self._in_buffer_lock, self._out_buffer_lock:
            self._stored_error = e
            set_payload((self._in_buffer[:], self._out_buffer[:]), e)

    # =========

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
                if received != None:
                    self._in_buffer = self._in_buffer + received
            except Exception as e:
                self.set_error_payload(e)
                self._alive = False

            self._in_buffer_updated.set()

    # ==============

    def write(self, data):
        with self._out_buffer_lock:
            if self._stored_error:
                raise self._stored_error
            self._out_buffer = self._out_buffer + data


    def _inner_write(self):
        with self._out_buffer_lock:
            try:
                if len(self._out_buffer) > 0:
                    written = self._raw_write(self._out_buffer)
                    self._out_buffer = self._out_buffer[written:]
            except Exception as e:
                self.set_error_payload(e)
                self._alive = False

            self._out_buffer_updated.set()
