
import numpy 
from types import *

from pygpu.GPU.gputypes import *

def typeOf(x):
    if hasattr(x, 'type'):
        return x.type

    elif type(x) == IntType:
        return Int

    elif type(x) == FloatType:
        return Float

#     elif type(x) == ListType or type(x) == TupleType:
#         n = len(x)
#         if n == 0:
#             return None
#         elif n == 1:
#             return Float
#         else:
#             return eval('Float%s' % n)

    elif numpy.isscalar(x) or type(x) is numpy.ndarray:
        ## !!FIXME!!  This code assumes all arrays contain floats
        s = numpy.shape(x)

        if len(s) > 1:
            raise TypeError("Cannot cast non rank-1 arrays yet: %s" % x)
        elif s != ():
            return eval('Float%s' % s[0])
        else:
            return Float

    elif hasattr(x, 'typecode'):
        tc = x.typecode()
        s = numpy.shape(x)

        if len(s) != 1:
            raise TypeError("Cannot cast non rank-1 arrays yet: %s" % x)

        if tc == 'l':
            return eval('Int%s' % s[0])
        elif tc == 'd':
            return eval('Float%s' % s[0])
        else:
            raise TypeError("Unknown type code '%s' in array" % tc)

    elif x is None:
        return GPUNone
    
    else:
        raise TypeError(str(x)) ##"When determining type for '%s'" % (x,))
        ## return None


