# Copyright 2023 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import numpy as np
import dimod

from helpers.filters import ALL_METHODS, apply_filters, compare_signals, create_filters
from dwave.samplers import SimulatedAnnealingSampler
from dwave.system import FixedEmbeddingComposite
from helpers.network import configure_network, create_channels, print_network_stats, simulate_signals

def loop_comparisons(qpu, runs=5, problem_size=16, snr=5, ratio=1.5, solvers=["matched_filter"]):
    """
    """

    if runs < 3:
        raise ValueError(f"Minimum supported runs is 3; got {runs}.")

    network, embedding = configure_network(
        lattice_size=problem_size, 
        ratio=ratio, qpu=qpu)
    print_network_stats(network)

    sampler_qpu = FixedEmbeddingComposite(qpu, embedding)
    sampler_sa = SimulatedAnnealingSampler()

    SNR=snr

    results = {'QPU': []}
    results.update({key: [] for key in solvers})
    print("Run number: ", end="")

    for run in range(runs):

        print(f"{run}, ", end="")
    
        channels, channel_power =  create_channels(network)
        y, transmitted_symbols = simulate_signals(channels, channel_power, SNRb=SNR)

        methods = set(ALL_METHODS) & set(solvers)
        filters = create_filters(channels, methods=methods)

        bqm = dimod.generators.mimo.spin_encoded_comp(network, 
            modulation = 'BPSK', 
            transmitted_symbols=transmitted_symbols, 
            F_distribution=('binary','real'), 
            F=channels,
            y=y)
    
        sampleset_qpu = sampler_qpu.sample(bqm, num_reads=30, 
            annealing_time=200, 
            chain_strength=-0.13*min(bqm.linear.values()), 
            label='Notebook - Coordinated Multipoint')

        results["QPU"].append(round(100*sum(np.array(list(sampleset_qpu.first.sample.values())) == transmitted_symbols.flatten())/len(transmitted_symbols)))
    
        v = apply_filters(y, filters)
        filter_results = compare_signals(v, transmitted_symbols, silent_return=True)
        for filter in methods:
            results[filter].append(filter_results[f'filter_{filter}'])

        if 'SA' in solvers:
            sampleset_sa = sampler_sa.sample(bqm, num_reads=1, num_sweeps=150)
            results['SA'].append(round(100*sum(np.array(list(sampleset_sa.first.sample.values())) == transmitted_symbols.flatten())/len(transmitted_symbols)))

    print("\n")

    return results