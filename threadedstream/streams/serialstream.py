import serial

from threadedstream.IoStream import IoStream

class SerialStream(IoStream):

    def __init__(self, port_name, baud_rate, separator='\n'):
        IoStream.__init__(self, separator=separator)

        self._serial = serial.Serial(port_name, baud_rate, write_timeout=0)


    def _raw_read(self, count=0):
        """ Count is ignored (instances do not maintain internal buffers)
        """
        byte_count = self._serial.in_waiting
        if byte_count:
            return self._serial.read(byte_count)


    def _raw_write(self, data):
        bytes_written = self._serial.write(data)
        self._serial.flush()

        return bytes_written
