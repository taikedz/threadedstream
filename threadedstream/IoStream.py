import os
from datetime import datetime
from typing import List, Tuple, Union, Callable

from threadedstream.Timer import Timer
from threadedstream import ThreadedStream
from threadedstream.NonBlockingStream import NonBlockingStream

class IoStream(ThreadedStream):
    """ Utility class that provides useful generic read and write operations backed by a ThreadedStream.

    It must receive a NonBlockingStream implementation that provides read_bytes() and write_bytes()
    methods.
    """
    def __init__(self, _nonb_stream:NonBlockingStream, tick=10e9, separator=os.sep):
        self._separator = separator

        ThreadedStream.__init__(self, _nonb_stream, tick)


    def read_until(self, target, timeout:float=None) -> Tuple(str, Exception):
        """ Read data until a target piece of data is encountered.

        This method blocks the calling thread until the target has been encountered.

        Returns a tuple of obtained data until and including the target, and any potential error.
        If the section times out, the error will be a throwable instance. Otherwise, it is None.
        """

        data = None

        def _update_local_buffer(new_data):
            data = new_data if data == None else data + new_data

        with Timer(timeout, f"read_until({repr(target)})") as t:
            while True:
                try:
                    t.check_timer()
                except TimeoutError as e:
                    return data, e

                # We check only after the buffer has had a chance to update.
                self._in_buffer_updated.wait()

                with self._in_buffer_lock:
                    # We acquire the lock overall, so that other threads
                    #  cannot modify the buffer between our check and our consumption
                    if self.contains(target):
                        idx = self.index(target)
                        _update_local_buffer(self.read(idx + len(target)) )
                        return data, None

                    # This thread is no longer alive. Get any remaining data.
                    elif self._alive != True:
                        _update_local_buffer( self.read(self.ready()) )
                        return data, EOFError(f"Reached end of stream before finding {repr(target)}")

                    else:
                        # If the target is longer than the available bytes, read zero bytes instead
                        max_data = max(0,  self.ready() - len(target))
                        _update_local_buffer(self.read())


    def read_line(self, timeout:float=None) -> Union[str,bytes]:
        """ Read a line of data from the stream.

        This method blocks the calling thread until a line is ready to be read.
        """
        line, err = self.read_until(self._separator, timeout)
        if err:
            raise err
        return line


    def read_lines(self, max_lines:int, skip:Callable=None, timeout:float=None) -> List[Union[str,bytes]]:
        """ Read max_lines number of lines, and return them.

        If `skip(L)` handler is provided, uses the skip function to determine
        whether to skip the line. Skipped lines do not count towards the max line count.
        """
        lines = []
        while len(lines) < max_lines:
            L = self.read_line()
            if skip_empty and skip(L): continue
            lines.append(L)
        return lines


    # Direct extensions to the ThreadedStream functionality

    def index(self, target):
        """ Look for the target in the incoming buffer, and return its index.

        Raises: ValueError - if target was not found
        """
        with self._in_buffer_lock:
            return self._in_buffer.index(target)


    def peek(self, count=32):
        """Look ahead without conuming bytes. Returns the first (count) bytes in the read buffer.
        """
        with self._in_buffer_lock:
            return self._in_buffer[:count]


    def ready(self) -> int:
        """ Return the number of bytes currently in the incoming buffer
        """
        with self._in_buffer_lock:
            return len(self._in_buffer)


    def contains(self, target) -> bool:
        """ Generally inexpensive operation to see that the
        target data is currently in the read buffer queue.

        Data that has been retrieved by read() is no longer in the queue
        """
        with self._in_buffer_lock:
            return target in self._in_buffer


    def check(self, check_operation) -> bool:
        """ Potentially expensive operation to apply a check
        function, which areceives a _copy_ of the data currently
        in the incoming bufffer.

        Expense is equal to the amount of data in the incoming buffer that needs copied.
        """
        with self._in_buffer_lock:
            return bool(check_operation(self._in_buffer[:]))


    def waiting(self) -> int:
        """ Return the number of bytes waiting still to be written out.
        """
        with self._out_buffer_lock:
            return len(self._out_buffer)
