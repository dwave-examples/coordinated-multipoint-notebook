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

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

import dwave_networkx as dnx

styles = {'QPU': 'b*', 'zero_forcing': 'g^', 'MMSE': 'mv', 'matched_filter': 'y>', 
    'SA': 'rx', 'greedy': 'cp', 'tabu': 'kD'}

def draw_network(network: nx.Graph):
    """Plot the given network.

    Args:
        network: Network graph.
    """
    if len(network) < 1000:
        fig = plt.figure(figsize=(8, 3))
    else:
        fig = plt.figure(figsize=(10, 10))

    tx = nx.get_node_attributes(network, 'num_transmitters')
    rx = nx.get_node_attributes(network, 'num_receivers')

    nx.draw_networkx(network, pos={n: n for n in network.nodes()}, 
        node_color = ['r' if tx[n] else 'g' if rx[n] else 'w' for n in network.nodes()], 
        with_labels=False, node_size=50)
    plt.show()

def draw_loop_comparison(results: dict, 
                         network_size: int = 16, 
                         ratio: float = 1.5, 
                         SNRb: float = 5):
    """Plot results of decoding comparisons.

    Args:
        results: results returned from other helper functions.

        network_size: Size of the network's underlying lattice.

        ratio: Ratio of transmitters to receivers.

        SNR: Signal-to-noise ratio.
    """
    fig = plt.figure(figsize=(8, 3))

    for key in results:
        plt.plot(results[key], styles[key], label=key, markersize=5)
        plt.plot(len(results[key])*[np.mean(results[key])], styles[key][0])

    plt.xlabel("Run")
    plt.ylabel("Success Rate [%]")
    plt.legend()
    plt.xticks(range(len(results[key])))    # All results are the same length (runs)
    plt.suptitle(f"Network size={network_size}, Tx/Rx$\\approx${ratio}, SNRb={SNRb}")
    plt.show()

def draw_instantiation_times(times: dict, network_sizes: dict):
    """Plot results of decoding comparisons.

    Args:
        times: Instantiations times, as a dict.

        network_sizes: Sizes of the underlying lattice.
    """

    fig = plt.figure(figsize=(8, 3))

    for key in times:
        plt.plot(times[key], styles[key] + '-', label=key, markersize=5)

    plt.xlabel("Network Size")
    plt.ylabel("Instantiation Time [ms]")
    plt.legend()
    plt.xticks(range(len(times[key])), labels=network_sizes)    
    plt.suptitle(f"Instantiation Times for Standard Linear Filters")
    plt.show()