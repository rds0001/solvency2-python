"""Offline Solvency II calculations with explicit inputs and documented limits."""
from . import _core

__version__ = _core.__version__
__all__ = list(_core.__all__)
globals().update({name: getattr(_core, name) for name in __all__})
