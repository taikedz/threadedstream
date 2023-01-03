from paramiko import SSHClient, MissingHostKeyPolicy
from paramiko.ssh_exception import SSHException

from threadedstream.IoStream import IoStream

class SshStream(IoStream):
    """ IoStream for a SSH session.

    Connect to a SSH target, and issue the initial command. This IoStream then remains open and readable for the duration of the command's activity.

    When writing to the stream, data is effectively sent to the initial command, which serves as the de facto interpreter itself..
    """

    def __init__(self, host, command="sh", username='root', password=None, port=22, accept_any_hostkey=False, separator='\n'):
        """ Start a SSH basic session, with an initial command/script.

        Use `command` (which can be a full shell script) to perform an initial action, like setting up
        an access to further subsystem behind the connection.

        The following
            stream = SshIoStream("Demo", "example.com", "bash /var/access_subsystem.sh")
            stream.write("SUBSYSTEM COMMAND")

        would be analogous to the shell equivalent
            echo "SUBSYSTEM COMMAND" | ssh example.com "bash /var/access_subsystem.sh"

        Do NOT attempt to perform your setup command(s) after the stream is instantiated, otherwise the
          ssh-side pipe will be mishandled.

        @param host: str - the hostname or IP address of the target system

        @param command: str - the command or shell script (sh) to execute as stream setup

        @param username: str - the SSH user name

        @param password: str - the SSH user password

        @param port: int - the SSH port

        @param accept_any_hostkey: bool - whether to ignore the fingerprint check
        """
        IoStream.__init__(self, separator=separator)

        self.__stderr_lock = threading.Lock()

        self._ssh = SSHClient.__init__(self)
        if accept_any_hostkey:
            self._ssh.set_missing_host_key_policy(AcceptHostPolicy())
        self._ssh.connect(host, username=username, port=port, password=password)

        (
            self._stdin,
            self._stdout,
            self._stderr,
        ) = self._ssh.exec_command(command)
        # `command` is sent and exec_command() returns immediately
        # we are ready to feed data into the SSH session


    def _raw_read(self, count=4096):
        out_chan = self._stdout.channel

        if out_chan.recv_ready():
            return out_chan.recv(count)


    def _raw_write(self, data):
        in_chan = self._stdin.channel

        if not in_chan.send_ready():
            return 0

        bytes_written = in_chan.send(data)
        return bytes_written


    def stderr_lines(self):
        """ Get any error stream output that has been seen.

        @return str - the lines of stderr data
        """
        err_chan = self._stderr.channel

        with self.__stderr_lock:
            data = []
            while err_chan.recv_stderr_ready():
                data.append( err_chan.recv_stderr(4096) )
            return b''.join(data)


    def _raw_close(self):
        self._ssh.close()



class AcceptHostPolicy(MissingHostKeyPolicy):
    """ A custom policy that doesn't modify the known_hosts
    Instead, this policy just allows any fingerprint from the server to be accepted,
    effectively cancelling the check.
    """
    def missing_host_key(self, *args, **kwargs):
        pass
