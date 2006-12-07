
class wrapWithHelper(object):
    def __init__(self, wrapper, f):
        self.wrapper = wrapper
        self.f = f

    def __call__(self, *args, **kwords):
        return self.wrapper(self.f(*args, **kwords))

class wrapWith(object):
    def __init__(self, f):
        self.wrapper = f

    def __call__(self, f):
        return wrapWithHelper(self.wrapper, f)
        
