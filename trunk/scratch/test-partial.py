
from copy import copy

class Partial:
    def __init__(self, func, kwords):
        self.func = func
        self.kwords = copy(kwords)

    def __call__(self, *args, **kwords):
        kwords2 = copy(self.kwords)
        kwords2.update(kwords)
        return self.func(*args, **kwords2)


class PartialHelper:
    def __init__(self, kwords = {}):
        self.kwords = copy(kwords)

    def __call__(self, *args, **kwords):
        kwords2 = copy(self.kwords)
        kwords2.update(kwords)
        return partial(*args, **kwords2)

def partial(*args, **kwords):
    if args:
        assert len(args) == 1
        return Partial(args[0], kwords)
    else:
        return PartialHelper(kwords)

@partial
def f(**kwords):
    print kwords

f()

@partial()
def f(**kwords):
    print kwords

f()

@partial(x="Test")
def f(**kwords):
    print kwords


f()
f(x="Calle")




