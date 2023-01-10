# Threaded Streams

A reference implementation allowing various types of concurrently executing streams, whilst maintaining thread safety and preventing data loss.

Typically useful if your script monitors a system's output via a connection, and in parallel performs actions to affect the running of the system in real-time.

Three examples of streams are implemented for reference: a serial stream (requires `serial`) for reading from serial connections such as on Raspberry Pi, a TCP stream for reading from raw TCP sockets, and a SSH stream (requires `paramiko`) for writing to the foreground process at the end of an SSH connection.

### Error payload - preventing data loss

During reading of data, it is possible for any mishap to occur, resulting in a runtime reading error. If at that point we still care about the contents of either the read buffer, or the outgoing buffer, this would typiclly be lost through the raising of an exception.

This library therefore implements the idea of an `error_payload` to allow recently acquired data to still be accessed, even when an exception is raised: any error raised by `ThreadedStream` is expected to carry a `error_payload` attribute on the exception instance matching a tuple of the input and output buffers at time of error.

[Write up an discussion on dev.to](https://dev.to/taikedz/an-exercise-in-multi-threading-and-lessons-learned-461m)

## Example

```python

from threadedstream.streams.sshstream import SshStream

s = SshStream("example.com", "user", "pass")
s.start()

# Send the command. The rest goes on in the background ...
s.write("bash long_script.sh\n")

# We might do some other stuff in the meantime ...

# .... and finally come back to this:
# Read from the buffer until we get the "Completed." message
try:
    script_logs = s.read_until("Completed.")
except Exception as e:
    # In case we got an error, we at least see the data
    print(f"Got an error. So far accumulated in the read buffer:\n{e.error_payload[0]}")

# Shorthand for clearing the read buffer
#  as we may not care about the remainder ?
s.consume_buffer()

```
