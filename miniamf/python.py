# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Python compatibility values and helpers.
"""

import builtins
import types

func_types = (
    types.BuiltinFunctionType, types.BuiltinMethodType, types.CodeType,
    types.FunctionType, types.GeneratorType, types.LambdaType, types.MethodType
)
class_types = [type]
int_types = [int]
str_types = [str]


int_types = tuple(int_types)
str_types = tuple(str_types)
class_types = tuple(class_types)

PosInf = 1e300000
NegInf = -1e300000
# we do this instead of float('nan') because windows throws a wobbler.
NaN = PosInf / PosInf


def isNaN(val):
    """
    @since: 0.5
    """
    return str(float(val)) == str(NaN)


def isPosInf(val):
    """
    @since: 0.5
    """
    return str(float(val)) == str(PosInf)


def isNegInf(val):
    """
    @since: 0.5
    """
    return str(float(val)) == str(NegInf)

def callable(obj):
    """
    Compatibility function for Python 3.x
    """
    return hasattr(obj, '__call__')
