
import pygpu.GPU.functions 

def isDummyIterator(it):
    return isinstance(it, pygpu.GPU.functions.DummyIterator)
