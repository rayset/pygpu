
__all__ = ['backend', 'chooseBackend']

import pygpu.backends.cg_backend

backend = None

def chooseBackend(_backend=None):
    global backend

    if _backend is None:
        print "Choosing backend...",
        backend = pygpu.backends.cg_backend.CgBackend()
        print "using Cg!"
    else:
        backend = _backend

    
