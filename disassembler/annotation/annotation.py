import re

ALL_ANNOTATIONS = {}

def annotation(handler):
    assert handler.__name__ not in ALL_ANNOTATIONS
    ALL_ANNOTATIONS[handler.__name__] = handler
    return handler

def callAnnotation(memory, addr, comment):
    kwargs = {}
    if " " in comment:
        handler_name, params = comment.split(" ", 1)
    else:
        handler_name, params = comment, ""

    for param in re.finditer("(\w+)=([^ ]+)", params):
        kwargs[param[1]] = param[2]
    
    handler = ALL_ANNOTATIONS.get(handler_name)
    if not handler:
        raise NotImplementedError("Encountered annotation: [@%s] but no implementation is found" % (comment))
    handler(memory, addr, **kwargs)
