
import numpy, sys

from pygpu.compiler.variable import isVar, TemporaryVariable, Constant
from pygpu.GPU.infer import typeOf
from pygpu.GPU.gputypes import *
from pygpu.GPU.operations import *

class DummyIterator:
    def __init__(self, type, start, stop, step):
        self.done = False
        self.start = start
        self.stop = stop
        self.step = step
        self.type = type

    def next(self):
        if self.done:
            raise StopIteration()
        else:
            self.done = True
            return obj

class range:
    def __init__(self, start, stop, step):
        self.start = start
        self.stop = stop
        self.step = step

    def __iter__(self):
        return DummyIterator(typeOf(self.start), self.start, self.stop, self.step)

    @staticmethod
    def call(*args):
        return __builtins__['xrange'](*args)

    @staticmethod
    def emit_call(block, start, stop=None, step=1):
        if stop is None:
            stop = start
            start = 0

        return range(start, stop, step)

class sqrt:
    def __init__(self, x):
        self.var = x
        
    @staticmethod
    def emit_call(block, x):
        return sqrt(x)
    
    @staticmethod
    def call(x):
        return numpy.sqrt(x)

class sum:
    @staticmethod
    def emit_call(block, x):
        #if len(x) == 0:
        #    raise TypeError("Cannot sum sequences of length 0")

        tmp = pygpu.compiler.variable.TemporaryVariable(typeOf(x[0]))
        block.add(GPUMov(tmp, x[0]))
        for v in x[1:]:
            tmp2 = pygpu.compiler.variable.TemporaryVariable(typeOf(v))
            block.add(GPUAdd(tmp2, tmp, v))
            tmp = tmp2

        return tmp

    @staticmethod
    def call(xs):
        return __builtins__['sum'](xs)

def unify(t1, t2):
    if t1 == t2:
        return t1

    f1 = t1.castTo(t2)
    f2 = t2.castTo(t1)
    if f1:
        return t2
    elif f2:
        return t1
    else:
        raise TypeError("cannot unify types '%s' and '%s'" % (t1,t2))
        

class mul:
    @staticmethod
    def emit_call(block, l, r):
        try:
            t = unify(typeOf(l), typeOf(r))
        except TypeError, e:
            raise TypeError("Cannot multiply %s and %s since '%s'" % (l,r,e))
                
        tmp = TemporaryVariable(t)
        block.add(GPUMul(tmp, cast(l, t), cast(r, t)))
        return tmp

class div:
    @staticmethod
    def emit_call(block, l, r):
        try:
            t = unify(typeOf(l), typeOf(r))
        except TypeError, e:
            raise TypeError("Cannot divide %s and %s since '%s'" % (l,r,e))
                
        tmp = TemporaryVariable(t)
        block.add(GPUDiv(tmp, cast(l, t), cast(r, t)))
        return tmp

class pow:
    @staticmethod
    def emit_call(block, l, r):
        assert typeOf(r) == Int
        tmp = TemporaryVariable(typeOf(l))
        block.add(GPUPow(tmp, l, r))
        return tmp


class round:
    @staticmethod
    def call(x):
        t = typeOf(x)
        if t == Float:
            return Constant(__builtin__['round'](x), t)
        elif t in [Float2, Float3, Float4]:
            return Constant(map(__builtin__['round'], x), t)
        else:
            raise TypeError("Cannot round variables of type %s" % t)

    @staticmethod
    def emit_call(block, x):
        tmp = TemporaryVariable(typeOf(x))
        block.add(GPUCall(tmp, "round", [x]))
        return tmp


class floor:
    @staticmethod
    def call(x):
        t = typeOf(x)
        if t == Float:
            return Constant(__builtin__['floor'](x), t)
        elif t in [Float2, Float3, Float4]:
            return Constant(map(__builtin__['floor'], x), t)
        else:
            raise TypeError("Cannot floor variables of type %s" % t)

    @staticmethod
    def emit_call(block, x):
        tmp = TemporaryVariable(typeOf(x))
        block.add(GPUCall(tmp, "floor", [x]))
        return tmp

class frac:
    @staticmethod
    def call(x):
        raise NotImplementedError()

    @staticmethod
    def emit_call(block, x):
        tmp = TemporaryVariable(typeOf(x))
        block.add(GPUCall(tmp, "frac", [x]))
        return tmp

class abs:
    @staticmethod
    def call(x):
        raise NotImplementedError()

    @staticmethod
    def emit_call(block, x):
        tmp = TemporaryVariable(typeOf(x))
        block.add(GPUCall(tmp, "abs", [x]))
        return tmp

    
class lerp:
    @staticmethod
    def call(x):
        raise NotImplementedError()

    @staticmethod
    def emit_call(block, a, b, x):
        ## !!FIXME!! implement type checking!
        tmp = TemporaryVariable(typeOf(a))
        block.add(GPUCall(tmp, "lerp", [a,b,x]))
        return tmp



class float2:
    @staticmethod
    def call(x, y):
        return Constant([x,y], Float2)

    @staticmethod
    def emit_call(block, x, y):
        tmp = TemporaryVariable(Float2)
        block.add(GPUCall(tmp, "float2", [x, y]))
        return tmp

class float3:
    @staticmethod
    def call(x, y, z):
        return Constant([x,y,z], Float3)

    @staticmethod
    def emit_call(block, x, y, z):
        tmp = TemporaryVariable(Float3)
        block.add(GPUCall(tmp, "float3", [x, y, z]))
        return tmp

class float4:
    @staticmethod
    def call(x, y, z, w):
        return Constant([x,y,z,w], Float4)

    @staticmethod
    def emit_call(block, x, y, z, w):
        tmp = TemporaryVariable(Float4)
        block.add(GPUCall(tmp, "float4", [x, y, z, w]))
        return tmp
