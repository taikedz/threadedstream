# Threaded Streams

A reference implementation allowing you to produce various types of concurrently executing streams, whilst maintaining thread safety.

Typically useful if your script monitors a system's output via a connection, and in parallel performs actions to affect the running of the system in real-time.

Three examples of streams are implemented for reference. Each can directly extend the `ThreadedStream` class , but the `IoStream` class is provided as a convenience for easier handling of managing read progress.

## Status

This is currently a Work In Progress. It is untested, unit tests have yet to be written.

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
script_logs = s.read_until("Completed.")

# Shorthand for clearing the buffer
# as we may not care about the remainder ?
s.consume_buffer()

```
