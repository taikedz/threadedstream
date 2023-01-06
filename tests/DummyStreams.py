""" Supporting constructs for testing the base functionality of
- ThreadedStream
- IoStream

see test_base_classes.py
"""

from threadedstream.IoStream import IoStream, ThreadedStream
from threadedstream.Timer import Timer


class TimedStream:
    def __init__(self, data_tick):
        self.__timer = Timer(None, "data clock")
        self.__gen_tick = data_tick
        self.__dummy_buffer = ''
        self.dt_reset()


    def dt_reset(self):
        self.__timer.start_timer()


    def dt(self):
        return self.__timer.check_timer()


    def _raw_read(self, count:int=4096) -> str:
        if self.dt() > self.__gen_tick:
            self.dt_reset()
            data = self.__dummy_buffer[:count]

            if data == '':
                return None

            self.__dummy_buffer = self.__dummy_buffer[count:]
            return data


    def _raw_write(self, data):
        self.__dummy_buffer += data
        return len(data)


class DummyThreaded(TimedStream, ThreadedStream):
    def __init__(self, data_tick):

        TimedStream.__init__(self, data_tick)
        ThreadedStream.__init__(self)


class DummyIo(TimedStream, IoStream):
    def __init__(self, data_tick):
        self.__dummy_buffer = ''

        TimedStream.__init__(self, data_tick)
        IoStream.__init__(self)
