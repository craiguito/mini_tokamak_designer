"""External solver adapter registry."""

from mini_tokamak.solvers.freegs_adapter import FreeGSAdapter
from mini_tokamak.solvers.fuse_adapter import FUSEAdapter
from mini_tokamak.solvers.openmc_adapter import OpenMCAdapter
from mini_tokamak.solvers.process_adapter import PROCESSAdapter
from mini_tokamak.solvers.tokamaker_adapter import TokaMakerAdapter
from mini_tokamak.solvers.torax_adapter import TORAXAdapter


def default_adapters():
    return [
        PROCESSAdapter(),
        FUSEAdapter(),
        FreeGSAdapter(),
        TokaMakerAdapter(),
        TORAXAdapter(),
        OpenMCAdapter(),
    ]

