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
from dwave.samplers import SimulatedAnnealingSampler, SteepestDescentSampler, TabuSampler
from dwave.system import FixedEmbeddingComposite
from helpers.network import configure_network, create_channels, print_network_stats, simulate_signals

def loop_comparisons(qpu, runs=5, network_size=16, snr=5, ratio=1.5, solvers=["matched_filter"]):
    """Compare decoding between multiple algorithms.

    Args:
        qpu: Quantum computer.

        runs: Number of problems to generate for comparisons.

        network_size: Size of the lattice underlying the network, 
            given as :math:`3*(network_size - 1)`.

        snr: Signal-to-noise ratio.

        solvers: Algorithms used to decode the transmission. 

    Returns:

        Results of the comparisons, as a dict.
    """

    if runs < 3:
        raise ValueError(f"Minimum supported runs is 3; got {runs}.")

    network, embedding = configure_network(
        network_size=network_size, 
        ratio=ratio, qpu=qpu)
    print_network_stats(network)

    sampler_qpu = FixedEmbeddingComposite(qpu, embedding)

    sampler_sa = SimulatedAnnealingSampler()
    sampler_sd = SteepestDescentSampler()
    sampler_tabu = TabuSampler()
      
    SNR=snr

    results = {'QPU': []}
    results.update({key: [] for key in solvers})
    print("Run number: ", end="")

    for run in range(runs):

        print(f"{run}, ", end="")
    
        channels, channel_power =  create_channels(network)
        y, transmitted_symbols = simulate_signals(channels, channel_power, SNRb=SNR)

        methods = set(ALL_METHODS).intersection(solvers)
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

        def avg(ss, ts):
            return round(100 * sum(np.array(list(ss.first.sample.values())) == ts.flatten()) / len(ts))
        
        results["QPU"].append(avg(sampleset_qpu, transmitted_symbols))
    
        v = apply_filters(y, filters)
        filter_results = compare_signals(v, transmitted_symbols, silent_return=True)
        for filter in methods:
            results[filter].append(filter_results[f'filter_{filter}'])

        # The next lines can be automated but the gain is not worth the complication
        if 'SA' in solvers:
            sampleset_sa = sampler_sa.sample(bqm, num_reads=1, num_sweeps=150)
            results['SA'].append(round(100*sum(np.array(list(sampleset_sa.first.sample.values())) == transmitted_symbols.flatten())/len(transmitted_symbols)))

        if 'greedy' in solvers:
            sampleset_sd = sampler_sd.sample(bqm, num_reads=1)
            results['greedy'].append(round(100*sum(np.array(list(sampleset_sd.first.sample.values())) == transmitted_symbols.flatten())/len(transmitted_symbols)))

        if 'tabu' in solvers:
            sampleset_tabu = sampler_tabu.sample(bqm, num_reads=1, timeout=30)
            results['tabu'].append(round(100*sum(np.array(list(sampleset_tabu.first.sample.values())) == transmitted_symbols.flatten())/len(transmitted_symbols)))

    print("\n")

    return results