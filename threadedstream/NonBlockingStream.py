from typing import Union

class NonBlockingStream:
    """ Referenceable type representing an implementation of a non-blocking wrapper for any stream.
    """

    def read(self, count:int=4096) -> Union[str,bytes]:
        """ Subclasses must implement this method.

        Implementation:

        - must not block when reading
        - must return at most `count` number of bytes
        - must not call ths superclass method
        """
        raise NotImplementedError("Override this method. Do not call it.")


    def write(self, data:Union[str,bytes]) -> int:
        """ Subclasses must implement this method.

        Implementation:

        - must not block to write
        - must return the number of bytes successfully written
        - must not call ths superclass method
        """
        raise NotImplementedError("Override this method. Do not call it.")
