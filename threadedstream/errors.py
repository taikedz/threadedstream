class StoppedThreadError(Exception): pass

def set_payload(payload, obj):
    setattr(obj, "error_payload", payload)

def re_raise_with(payload, error):
    """ In an `except:` block, call this function to attach the
    given payload to the exception.
    """
    set_payload(payload, error)
    raise