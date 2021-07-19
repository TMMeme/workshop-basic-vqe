from typing import Dict
import json
import yaml
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from zquantum.core.wip.circuits import import_from_qiskit
from zquantum.core.utils import create_object
from zquantum.core.interfaces.backend import QuantumBackend

def build_ansatz(param: Parameter) ->QuantumCircuit:
    ansatz = QuantumCircuit(1,1)
    ansatz.ry(param, 0)
    return ansatz

def build_circuits() ->Dict[str, QuantumCircuit]:
    zcircuit = QuantumCircuit(1, 1)

    xcircuit = QuantumCircuit(1, 1)
    xcircuit.h(0)

    ycircuit = QuantumCircuit(1, 1)
    ycircuit.u(np.pi/2, 0, np.pi/2, 0)

    return {
        "x": xcircuit,
        "y": ycircuit,
        "z": zcircuit,
    }

