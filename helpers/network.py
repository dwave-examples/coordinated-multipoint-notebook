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

from typing import Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import random

import dimod
import dwave_networkx as dnx


def _num_tx_rx(network: nx.Graph) -> Tuple[int, int]:
    """"Get the number of transmitters and receivers in the given network.

    Args:
        network: Network graph.

    Returns:
        Two-tuple of numbers of transmitters and receivers. 
    """
    num_tx = sum(nx.get_node_attributes(network, "num_transmitters").values())
    num_rx = sum(nx.get_node_attributes(network, "num_receivers").values())

    return num_tx, num_rx

def _node_to_chain(row: int, col: int) -> Tuple[
    Tuple[int, int, int, int], Tuple[int, int, int, int]]: 
    """"Embed a node into a chain for a grid-with-diagonal lattice.

    Args:
        row: Row in the lattice.

        col: Column in the lattice.

    Returns:
        Two-tuple of the two nodes, in Pegasus coordinates, that constitute a
            chain representing the given node. 

    References:
    
    * https://arxiv.org/pdf/2003.00133.pdf Table 1
    """
    row_par = row%3
    col_par = col%3
    x = col//3
    y = row//3
    if row_par == 0:
        if col_par == 0:
            return (0, x, 2, y), (1 ,y, 7, x)
        elif col_par == 1:
            return (0, x+1, 0, y), (1, y, 2, x)
        else:
            return (0, x+1, 3, y), (1, y, 8, x)
    elif row_par == 1:
        if col_par == 0:
            return (0, x, 8, y), (1, y, 6, x)
        elif col_par == 1:
            return (0, x, 11, y), (1, y+1, 0, x)
        else:
            return (0, x, 10, y), (1, y, 11, x)
    else:
        if col_par == 0:
            return (0, x, 7, y), (1, y+1, 4, x)
        elif col_par == 1:
            return (0, x, 6, y), (1, y+1, 3, x)
        elif col_par == 2:
            return (0, x+1, 4, y), (1, y, 10, x)

# Maintained here until Jack adds a general embedding algo to minorminer 
def _create_lattice(network_size: int = 16, 
                    qpu: dimod.sampler = None) -> Tuple[dict, nx.Graph]:
    """Create a lattice with an embedding

    Args:
        network_size: Size of the lattice underlying the network, 
            given as :math:`3*(network_size - 1)`. 
        qpu: QPU to which the network graph must be compatible.

    Returns:
        Two tuple of embedding and the source lattice. 
    """
    p16_graph = dnx.pegasus_graph(m=16, nice_coordinates=True)
    node_list = [
        dnx.pegasus_coordinates(16).nice_to_linear(node) for node in p16_graph.nodes if 
        node[1]<network_size and node[2]<network_size]
    edge_list = None

    if qpu:
        node_list = list(set(node_list).intersection(qpu.nodelist))
        edge_list = qpu.edgelist
        
    qpu_graph = dnx.pegasus_graph(m=16, node_list=node_list, edge_list = edge_list)

    target = nx.relabel_nodes(qpu_graph, 
        {n: dnx.pegasus_coordinates(16).linear_to_pegasus(n) 
        for n in qpu_graph.nodes()})

    scale = 3*(network_size - 1)
    emb = {}
    source = nx.Graph()
    sourceF = nx.Graph()
    node_defects = 0
    edge_defects = 0
    for row in range(scale):
        for col in range(scale):
            v = (row, col)
            edge = _node_to_chain(row, col)
            sourceF.add_node(v)
            for delta in [(0, -1), (-1, 0), (-1, -1), (-1, 1)]:
                v_back = (row + delta[0], col + delta[1])
                if sourceF.has_node(v_back):
                    sourceF.add_edge(v, v_back)
            if target.has_edge(*edge):
                emb[v] = edge
                source.add_node(v)
                #Add backwards:
                for delta in [(0, -1), (-1, 0), (-1, -1), (-1, 1)]:
                    v_back = (row + delta[0], col + delta[1])
                    if source.has_node(v_back):
                        if any(target.has_edge(v1, v2) 
                                for v1 in emb[v] for v2 in emb[v_back]):
                            source.add_edge(v, v_back)
                        else:
                            edge_defects += 1
                            source.remove_node(v_back)
                            del emb[v_back]
                    else:
                        pass
            else:
                node_defects += 1

    return emb, source

def configure_network(network_size: int = 16, 
                      qpu: dimod.sampler = None, 
                      ratio: float = 1.5) -> Tuple[nx.Graph, dict]:
    """Configure network transmitters and receivers.

    Args:
        network_size: Size of the underlying lattice, :math:`3*(network_size - 1)`. 
            Supported values are integers between 4 to 16. 
        
        qpu: QPU to which the graph must be compatible.

        ratio: Required Tx/Rx ratio. A best-effort attempt is made to "turn off"
            a random selection of most-connected receivers to achieve the requested 
            ratio.

    Returns:
        Two-tuple of network graph and minor-embedding. 
    """
    if network_size not in range(2, 17):
        raise ValueError("Supported lattice sizes are between 4 to 16")		

    emb, source = _create_lattice(network_size=network_size, qpu=qpu)

    network = nx.Graph()
    network.add_nodes_from(source.nodes())
    
    nx.set_node_attributes(network, values=1,  name='num_transmitters')
    nx.set_node_attributes(network, values=0, name='num_receivers')

    # Add receiver nodes 
    for n in list(network.nodes()):
        network.add_nodes_from(((n[0]+x, n[1]+y) for x in [-0.5,0.5] for y in [-0.5,0.5]),
            num_receivers=1,
            num_transmitters=0)
        
        network.add_edges_from((n,(n[0]+x, n[1]+y)) 
            for x in [-0.5,0.5] for y in [-0.5,0.5])

    # Remove boundary receivers (no ISI)
    left_bound = min(network.nodes())[0] 
    top_bound = max(network.nodes())[0]  
    for n in network.nodes():
        if n[0] == left_bound or n[0] == top_bound or n[1] == left_bound or n[1] == top_bound:
            network.nodes[n]['num_receivers'] = 0

    # Dilute receivers to approximately the requested Tx/Rx ratio
    rx_nodes = [n for n, v in nx.get_node_attributes(network, "num_receivers").items() if v==1]
    tx_nodes = [n for n, v in nx.get_node_attributes(network, "num_transmitters").items() if v==1]
    num_tx = len(tx_nodes)
    num_rx = len(rx_nodes)   
    num_rx_to_delete = int(num_rx - num_tx/ratio) 
    while num_rx_to_delete > 0.02*num_tx:
        adj_tx_adj_rx = {rx: sum(sum(network.nodes[n]['num_receivers'] for n in network.adj[tx]) 
            for tx in [tx for tx in network.adj[rx].keys()]) 
                for rx in rx_nodes}
        rx_max_adj_rx = [rx for rx, v in adj_tx_adj_rx.items() if v == max(adj_tx_adj_rx.values())]
        rx_to_delete = random.sample(rx_max_adj_rx, min(len(rx_max_adj_rx), int(0.02*num_tx)))
        nx.set_node_attributes(network.subgraph(rx_to_delete), values=0, name='num_receivers')         
        rx_nodes = [n for n, v in nx.get_node_attributes(network, "num_receivers").items() if v==1]
        num_rx_to_delete = int(len(rx_nodes) - num_tx/ratio)
        
    # Prevent disconnected transmitters 
    for tx in tx_nodes:
        num_rx_neighbors = sum(network.nodes[n]['num_receivers'] for n in network.adj[tx])
        if num_rx_neighbors == 0:
            candidates = [n for n in network.adj[tx] if network.nodes[n]['num_receivers'] == 0]
            add_rx = candidates[np.random.randint(0, len(candidates))]
            network.nodes[add_rx]['num_receivers'] = 1
    
    emb = {idx: [dnx.pegasus_coordinates(16).pegasus_to_linear(n[0]), 
                dnx.pegasus_coordinates(16).pegasus_to_linear(n[1])] for 
                idx, (tx, n) in enumerate(emb.items())}

    return network, emb

def print_network_stats(network: nx.Graph):
    """Print statistics on the network graph.

    Args:
        network: Network graph.
    """
    num_tx, num_rx = _num_tx_rx(network) 
    tx_over_rx = num_tx/num_rx
	
    print(f"Ratio of transmitters to receivers: {round(tx_over_rx, 2)}.")
    print(f"Network has {num_tx} transmitters and {num_rx} receivers", 
          f"with {len(network.edges)} edges.")

def create_channels(
    network: nx.Graph, 
    F_distribution: Tuple[str, str] = ("binary", "real"), 
    attenuation_matrix: np.ndarray = None) -> Tuple[np.ndarray, float]:
    """Create a matrix representing the network transmission channels. 

    Args:

        network: Network graph.

        F_distribution: Zero-mean, variance-one distribution, in tuple form 
            ``(distribution, type)``, used to generate each element in the 
            channels. Supported values are:
            
            * ``'normal'`` or ``'binary'`` for the distribution. 
            * ``'real'`` or ``'complex'`` for the type. 

        attenuation_matrix: Root-power part of the channels matrix. 

    Returns:
        Two tuple of the channels and channel power. 
        
    """
    num_tx, num_rx = _num_tx_rx(network)
    am = dimod.generators.wireless._lattice_to_attenuation_matrix(network)[0]

    return dimod.generators.wireless.create_channel(
        num_receivers=num_rx, 
        num_transmitters=num_tx, 
        F_distribution=F_distribution,
        attenuation_matrix=am)

def simulate_signals(
    channels: np.ndarray, 
    channel_power: float, 
    transmitted_symbols: np.ndarray = None, 
    SNRb: float = float('Inf')) -> Tuple[np.ndarray, np.ndarray]:
    """Simulate transmitted signal.

    Args:
        channels: Transmission channels for the transmitted symbols.

        channel_power: Power of the channels.

        transmitted_symbols: Symbols generated by the transmitters.

        SNRb: Signal-to-noise ratio.

    Returns:
        Two tuple of received and transmitted signals. 
    """
    if not transmitted_symbols:
        num_tx = channels.shape[1]
        transmitted_symbols = np.random.choice([1, -1], size=[num_tx, 1]) 

    y, v, _, _ = dimod.generators.wireless._create_signal(channels, 
        transmitted_symbols=transmitted_symbols,
        channel_power=channel_power,
        SNRb=SNRb)

    return y, v