import socket

from threadedstream.IoStream import IoStream

class TcpStream(IoStream):

    def __init__(self, host, port, separator=b'\x00'):
        IoStream.__init__(self, separator=separator)

        self.__io_stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__io_stream.connect((host, port))
        # Set zero for a non-blocking behaviour
        self.__io_stream.settimeout(0.0)


    def _raw_read(self, count=512):
        new_data = None

        try:
            new_data = self.__io_stream.recv(size)

        except socket.error as e:
            # The read operation will raise an error if nothing is available
            # we want to silently catch this for the "non-blocking" effect
            if ( not ("Resource temporarily unavailable" in str(e) or
                      "A non-blocking socket operation could not be completed immediately" in str(e)
                )):
                raise

        return new_data


    def _raw_write(self, data):
        # 'send' may possibly only send a subset of data
        #  to ensure we are non-blocking, just return the size of
        #  whatever was effectively written
        bytes_written = self.__io_stream.send(data)
        return bytes_written


    def _raw_close(self):
        self.__io_stream.close()
