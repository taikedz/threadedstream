from unittest import TestCase
import time

from tests.DummyStreams import DummyIo, DummyThreaded

class TestDummyThreaded(TestCase):
    def __init__(self, name):
        TestCase.__init__(self, name)
        self.stream = DummyThreaded(0.1)
        # Slow down the thread tick rate for debugging
        #self.stream._tick = 0.1
        self.stream.start()


    def test_write(self):
        self.stream.write("hello\n")
        time.sleep(0.2)
        assert self.stream.read() == "hello\n"
        assert self.stream.read() == ""


class TestDummyIo(TestCase):
    def __init__(self, name):
        TestCase.__init__(self, name)
        self.stream = DummyIo(0.1)
        # Slow down the thread tick rate for debugging
        self.stream._tick = 0.1
        self.stream.start()


    def test_write(self):
        self.assertRaises(TimeoutError, self.stream.read_until, "cats", 1)

        self.stream.write("There are cats. And dogs.\n")
        time.sleep(0.3)
        assert self.stream.read_until("cats", 1) == "There are cats"
        assert self.stream.read_line(timeout=0.1) == ". And dogs.\n"

        self.stream.write("Waiting for")
        time.sleep(0.3)
        try:
            self.stream.read_until("Godot", 0.2)
        except TimeoutError as e:
            assert hasattr(e, "error_payload")
            assert e.error_payload == "Waiting for"


        self.stream.write("One\nTwo\nThree")
        time.sleep(0.2)
        assert self.stream.read_lines(2, timeout=0.1) == ["One\n", "Two\n"]
        assert self.stream.consume_buffer() == "Three"