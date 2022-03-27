import re

ALL_ANNOTATIONS = {}

def annotation(handler=None, *, priority=100):
    if handler == None:
        def f(handler):
            annotation(handler, priority=priority)
        return f
    assert handler.__name__ not in ALL_ANNOTATIONS
    ALL_ANNOTATIONS[handler.__name__] = handler
    handler.priority = priority
    return handler

def getAnnotation(memory, addr, comment):
    kwargs = {}
    args = []
    if " " in comment:
        handler_name, params = comment.split(" ", 1)
    else:
        handler_name, params = comment, ""

    for param in params.split(" "):
        if "=" in param:
            param = param.split("=", 1)
            kwargs[param[0]] = param[1]
        elif param != "":
            args.append(param)
    
    handler = ALL_ANNOTATIONS.get(handler_name)
    if not handler:
        raise NotImplementedError("Encountered annotation: [@%s] but no implementation is found" % (comment))
    def f():
        handler(memory, addr, *args, **kwargs)
    f.priority = handler.priority
    return f
