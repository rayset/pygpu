
import pygpu.GPU.infer
import pygpu.GPU.gputypes 
import pygpu.compiler.variable

def comparisonType(l,r):
    tl = pygpu.GPU.infer.typeOf(l)
    tr = pygpu.GPU.infer.typeOf(r)

    if tl != tr:
        raise TypeError("Cannot compare variables of different type!")

    try:
        return eval('pygpu.GPU.gputypes.Bool%s' % tl.shape[0])
    except AttributeError:
        return pygpu.GPU.gputypes.Bool


class GPUOp(object):
    def __init__(self, name, *args):
        self.name = name
        self.args = args

    def __str__(self):
        return "%s %s;" % (self.name,
                           ", ".join(map(str, self.args)))

    def emit(self, emitter):
        return getattr(emitter, self.name)(*self.args)



def GPUMov(t,s):
    return GPUOp("Mov", t, s)

def GPUAdd(t,l,r):
    return GPUOp("Add", t, l, r)

def GPUSub(t,l,r):
    return GPUOp("Sub", t, l, r)

def GPUMul(t,l,r):
    return GPUOp("Mul", t, l, r)

def GPUDiv(t,l,r):
    return GPUOp("Div", t, l, r)

def GPUPow(t,l,r):
    return GPUOp("Pow", t, l, r)

def GPUIf(c):
    return GPUOp("If", c)

def GPUElse():
    return GPUOp("Else")

def GPUEndIf():
    return GPUOp("EndIf")

def GPURet(v):
    return GPUOp("Ret", v)

def GPULt(l,r):
    t = comparisonType(l,r)
    tmp = pygpu.compiler.variable.TemporaryVariable(t)
    return tmp, GPUOp("Lt", tmp, l, r)
    
def GPULe(l,r):
    type = comparisonType(l,r)
    tmp = pygpu.compiler.variable.TemporaryVariable(type)
    return tmp, GPUOp("Le", tmp, l, r)
    
def GPUEq(l,r):
    type = comparisonType(l,r)
    tmp = pygpu.compiler.variable.TemporaryVariable(type)
    return tmp, GPUOp("Eq", tmp, l, r)

def GPUNe(l,r):
    type = comparisonType(l,r)
    tmp = pygpu.compiler.variable.TemporaryVariable(type)
    return tmp, GPUOp("Ne", tmp, l, r)

def GPUGt(l,r):
    type = comparisonType(l,r)
    tmp = pygpu.compiler.variable.TemporaryVariable(type)
    return tmp, GPUOp("Gt", tmp, l, r)

def GPUGe(l,r):
    type = comparisonType(l,r)
    tmp = pygpu.compiler.variable.TemporaryVariable(type)
    return tmp, GPUOp("Ge", tmp, l, r)

def GPUIn(l,r):
    raise NotImplementedError()

def GPUNotIn(l,r):
    raise NotImplementedError()

def GPUIs(l,r):
    raise NotImplementedError()

def GPUIsNot(l,r):
    raise NotImplementedError()

def GPUExceptionMatch(l,r):
    raise NotImplementedError()

def GPUBAD(l,r):
    raise NotImplementedError()

def GPUBeginLoop(i, it):
    return GPUOp("BeginLoop", i, it)

def GPUEndLoop():
    return GPUOp("EndLoop")
    
def GPUUNeg(tmp, x):
    return GPUOp("UNeg", tmp, x)
    
def GPUSample(tmp, tex, p, filterMode):
    return GPUOp("Sample", tmp, tex, p, filterMode)

def GPUCall(tmp, funcName, args):
    return GPUOp("Call", tmp, funcName, args)
