import os
from datetime import datetime
from typing import List, Tuple, Union, Callable

from threadedstream.Timer import Timer
from threadedstream.ThreadedStream import ThreadedStream
from threadedstream.errors import re_raise_with, set_payload


class IoStream(ThreadedStream):
    """ Convenience class that provides useful generic read and write operations backed by a ThreadedStream.
    """
    def __init__(self, tick=10e6, separator=os.linesep):
        self._separator = separator

        ThreadedStream.__init__(self, tick)


    def read_until(self, target, timeout:float=None) -> Tuple[str, Exception]:
        """ Read data until a target piece of data is encountered.

        This method blocks the calling thread until the target has been encountered.

        Any errors raised will have an additional special property `error_payload` containing
         the data accumulated by the time of the error. 
        """

        data = None

        def _update_local_buffer(new_data):
            nonlocal data
            data = new_data if data == None else data + new_data

        with Timer(timeout, f"read_until({repr(target)})") as t:
            while True:
                try:
                    t.check_timer()

                    # We check only after the buffer has had a chance to update.
                    self._in_buffer_updated.wait()

                    with self._in_buffer_lock:
                        # We acquire the lock overall, so that other threads
                        #  cannot modify the buffer between our check and our consumption
                        if self.contains(target):
                            idx = self.index(target)
                            _update_local_buffer(self.read(idx + len(target)) )
                            return data

                        # This thread is no longer alive. Get any remaining data, and raise.
                        elif self._alive != True:
                            _update_local_buffer( self.read(self.ready()) )
                            raise EOFError(f"Reached end of stream before finding {repr(target)}")

                        else:
                            # If the target is longer than the available bytes, read zero bytes instead
                            max_data = max(0,  self.ready() - len(target))
                            _update_local_buffer(self.read())

                except Exception as e:
                    if hasattr(e, "error_payload"):
                        if isinstance(e.error_payload, tuple):
                            # A lower-level ThreadedStream error occurred
                            # It already contains its own payload. Restore our data to it
                            set_payload((data+e.error_payload[0], e.error_payload[1]))
                            raise
                    re_raise_with((data+self._in_buffer, self._out_buffer), e)


    def read_line(self, timeout:float=None) -> Union[str,bytes]:
        """ Read a line of data from the stream.

        This method blocks the calling thread until a line is ready to be read.

        Any errors raised will have an additional special property `error_payload` containing
         the data accumulated by the time of the error. 
        """
        return self.read_until(self._separator, timeout)


    def read_lines(self, max_lines:int, skip:Callable=None, timeout:float=None, line_timeout:float=0.1) -> List[Union[str,bytes]]:
        """ Read max_lines number of lines, and return them.

        Must always have a maximumm number of lines, as stremas are presumed infinite. If you indeed expect
         to read all lines of the stream until EOF, set max_lines=0

        If `skip(L)` handler is provided, uses the skip function to determine
        whether to skip the line. Skipped lines do not count towards the max line count.

        Any errors raised will have an additional special property `error_payload` containing
         the data accumulated by the time of the error. 

        max_lines: read this many lines before returning
        timeout : max time to allow for reading all lines
        line_timeout: max time to allow for reading any single line
        """
        lines = []
        try:
            with Timer(timeout, f"read_lines({max_lines})") as t:
                while len(lines) < max_lines or max_lines == 0:
                    t.check_timer()
                    L = self.read_line(line_timeout)
                    if skip != None and skip(L): continue
                    lines.append(L)
                return lines

        except Exception as e:
            if hasattr(e, "error_payload"):
                if isinstance(e.error_payload, tuple):
                    # A lower-level ThreadedStream error occurred
                    # It already contains its own payload. Restore our data to it
                    set_payload((data+e.error_payload[0], e.error_payload[1]))
                    raise
                else:
                    # Error payload single line before it was tracked
                    lines.append(e.error_payload)
            data = self._separator.join(lines)
            re_raise_with((data+self._in_buffer, self._out_buffer), e)


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


    def consume_buffer(self) -> Union[str,bytes]:
        """ Consume current buffer and return it.
        """
        return self.read(self.ready())


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
