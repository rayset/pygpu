import numpy
from types import *

from pygpu.utils import all
from pygpu.GPU.infer import typeOf
from pygpu.GPU.gputypes import *

class Variable(object):
    def __init__(self, name, type):
	self.name = name
	self.type = type

    def __str__(self):
	return "%s" % (self.name)

    def __getitem__(self, i):
        if isinstance(i, IntType):
            return Swizzle(Float, self, [i])

        elif isinstance(i, slice):
            start,stop,step = i.start, i.stop, i.step
            if stop is None:
                stop = start
                start = 0
            if step is None:
                step = 1
            n = (stop-start)/step
            return Swizzle(eval('Float%d' % n), self, range(start,stop,step))

        else:
            raise NotImplementedError()

    def __len__(self):
        return len(self.type)

class LocalVariable(Variable):
    def __init__(self, name, type = None):
        Variable.__init__(self, name, type)

    def __str__(self):
        if self.type is None:
            return "?Unknown type?(%s)" % self.name
        else:
            return Variable.__str__(self)

class ArgumentVariable(LocalVariable):
    def __init__(self, name, type):
        LocalVariable.__init__(self, name, type)

    def emit_call(self, block, *args):
        return self.type.emit_call(block, self, *args)
        

_swizzles = ['x','y','z','w']

class Swizzle(object):
    def __init__(self, type, var, swizzle):
        self.var = var
        self.type = type
        self.swizzle = swizzle

        assert len(swizzle) == len(type)

    def __str__(self):
        return "<swizzle %s %s %s>" % (self.type, self.var, self.swizzle)

class TemporaryVariable(Variable):
    _noTemps = 0

    def __init__(self, type):
        Variable.__init__(self, "tmp_%s" % self._noTemps, type)
        TemporaryVariable._noTemps += 1

def isVar(x):
    return isinstance(x, Variable)
    #    return True
    # elif isinstance(x, Swizzle):
        

class Constant(object):
    def __init__(self, value, type = None):
        self.value = value
        if type is None:
            type = typeOf(value)
        self.type = type
            
    def __str__(self):
	return "%s(%s)" % (self.type, self.value)

    def __add__(self, other):
        assert isinstance(other, Constant)
        return Constant(self.value + other.value)

    def __getitem__(self, i):
        return self.value[i]
    


def isSequence(x): ## -> Bool
    """ Determines if x is a sequence """
    return type(x) in [TupleType,ListType]

def isConstant(x): ## -> Bool
    ## return isinstance(x, pygpu.compiler.variable.Constant)
    if numpy.isscalar(x) or type(x) is numpy.ndarray:
        return True
    elif isinstance(x, Constant):
        return True
    elif isSequence(x):
        return all(isConstant, x, True)
    else:
        return False

def isTemporary(x):
    return isinstance(x, TemporaryVariable)

def isSwizzle(x):
    return isinstance(x, Swizzle)

def stripConstant(x):
    if isinstance(x, Constant):
        return x.value
    elif isSequence(x):
        return map(stripConstant, x)
    elif numpy.isscalar(x) or type(x) is numpy.ndarray:
        return x
    else:
        print "WARNING:", x, "is not a constant!"
        return x
