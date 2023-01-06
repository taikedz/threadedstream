from datetime import datetime

class Timer:
    """ Context-managed timer to assist detecting elapsed time.

    If a timeout is specified as a float or int, the check_timeout() method will throw TimeoutError

    If a timeout is specified as None, no timeout error is raised.

    This allows it to be used in various scenarios:

    Ensuring a loop does not exceed a given amount of time - note that the loop's operation must not
    block, otherwise timeout check cannot happen.

    ```python
    with Timer(timeout=10) as t:
        while True:
            do_thing() # Must be non-blocking
            t.check_timer() # Will error out if timeout exceeded
    ```

    Or, simply getting an elapsed clock time report:

    ```python
    with Timer(timeout=None) as t:
        do_stuff()

    print(f"Took {t.check_timeer()}s to run operation.")
    ```
    """
    def __init__(self, timeout:float, name:str=None):
        self.__timeout:float = timeout
        self.__dt:float = 0
        self.__start:datetime = None
        self.__name:str = "unnamed timer" if name == None else name


    def check_timer(self):
        """ Check how much time has elapsed.

        If elapsed time is greater than declared timeout, raises TimeoutError.

        Returns elapsed time. If timer was stopped previously, elapsed time is as when it was stopped.
        """
        if self.__start != None:
            self.__dt = (datetime.now() - self.__start).total_seconds()
            if self.__timeout != None and self.__dt >= self.__timeout:
                raise TimeoutError(f"{self.__name} timed out beyond {self.__timeout}s (at {self.__dt}s)")
        return self.__dt


    def start_timer(self):
        self.__start = datetime.now()


    def stop_timer(self):
        self.__start = None


    def __enter__(self):
        self.start_timer()
        return self


    def __exit__(self, *e):
        self.stop_timer()
    