from steps.solution import expectation_from_circuit
from typing import Dict
import json
from numpy.core.fromnumeric import argmin
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

def vqe(backend_specs, coefficients, min_value=0, max_value = 2 * np.pi):
    if isinstance(backend_specs, str):
        backend_specs_dict = yaml.load(backend_specs, Loader=yaml.SafeLoader)
    else:
        backend_specs_dict = backend_specs
    backend = create_object(backend_specs_dict)

    if isinstance(coefficients, str):
        coefficients_dict=yaml.load(coefficients, Loader=yaml.SafeLoader)
    else:
        coefficients_dict = coefficients
    
    theta = Parameter("θ")
    ansatz = build_ansatz(theta)
    circuits = build_circuits()

    #Search over our input parameters
    results, values = search(
        backend,
        ansatz,
        theta,
        circuits,
        coefficients_dict,
        min_value=min_value,
        max_value=max_value,
    )

    minimum_idx = np.argmin(results)

    data = {
        "minimum": {
            "value": results[minimum_idx],
            "theta": values[minimum_idx],
        },
        "results": results,
        "values": values.tolist(),
    }

    with open("results.json", "w") as f:
        json.dump(data, f)

def search(
    backend: QuantumBackend,
    ansatz: QuantumCircuit,
    param: Parameter,
    circuits: Dict[str, QuantumCircuit],
    coefficients: Dict[str, int],
    min_value=0,
    max_value=1,
    samples=10000,
):
    
    #Create our search space
    values = np.linspace(min_value, max_value, 100)

    results = []

    #Loop over all points in out search space
    #In real VQE workloads, you want to use an optimizer here
    for v in values:
        energy =0
        #Loop over each coefficient
        for k, coef in coefficients.items():
            # Skip if the coefficient is 0
            if coef == 0:
                continue

            #Only run a circuit if we are not considering the "I" part of the Hamiltonian
            if k !="i":
                energy += estimate_energy(
                    backend, coef, ansatz, param, v, circuits[k], samples
                )
            else:
                energy += coef
        #Keep track of this total energy
        results.append(energy)
    #return all the calculated energies and parameter values
    return results, values

def estimate_energy(backend, coef, ansatz, param, value, measure_circuit, samples):
    #Combine the Ansatz and measurement circuits
    circuit = ansatz + measure_circuit
    #Replace the Parameter with a value
    circuit = circuit.bind_parameters({param: value})
    #Take the expectation value, multiple by the coefficient, and to our energy value
    return coef * expectation_from_circuit(backend, circuit, samples)


def expectation_from_circuit(
    backend: QuantumBackend, circuit:QuantumCircuit, samples: int):

    #Convert the qiskit circuit
    zap_circuit = import_from_qiskit(circuit)

    #Execute the circuit using an Orquestra backend
    measurement = backend.run_circuit_and_measure(zap_circuit, n_samples=samples)
    counts = measurement.get_counts()

    #Estimate the expectation value based on the counts
    expectation_value = 0
    for bit, count in counts.items():
        sign = +1
        if bit =="1":
            sign = -1
        expectation_value += sign * count / samples
    return expectation_value
