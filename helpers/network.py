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
import dimod
import dwave_networkx as dnx


def num_tx_rx(network):
    num_tx = sum(nx.get_node_attributes(network, "num_transmitters").values())
    num_rx = sum(nx.get_node_attributes(network, "num_receivers").values())
    return num_tx, num_rx

def _node_to_chain(row, col): 
    """"Embed a node into a chain for a grid-with-diagonal lattice.

    Args:
        row: Row, as an integer, in the lattice.

        col: Column, as an integer, in the lattice.

    Returns:
        Two-tuple of the two nodes, in Pegasus coordinates that constitute a
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

def _create_lattice(lattice_size=16, qpu=None):
    """Create a lattice with an embedding

    Args:
        lattice_size: Size of the lattice. 

    Returns:
        Two tuple of embedding and the source lattice. 
    """
    p16_graph = dnx.pegasus_graph(m=16, nice_coordinates=True)
    node_list = [dnx.pegasus_coordinates(16).nice_to_linear(node) 
        for node in p16_graph.nodes if 
        node[1]<lattice_size and node[2]<lattice_size]
    edge_list = None

    if qpu:
        node_list = list(set(node_list) & set(qpu.nodelist))
        edge_list = qpu.edgelist
        
    qpu_graph = dnx.pegasus_graph(m=16, node_list=node_list, edge_list = edge_list)

    target = nx.relabel_nodes(qpu_graph, 
        {n: dnx.pegasus_coordinates(16).linear_to_pegasus(n) 
        for n in qpu_graph.nodes()})

    scale = 3*(lattice_size - 1)
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

def configure_network(lattice_size=16, qpu=None, ratio=1):
    """Configure network transmitters and receivers.

    Args:
        lattice_size: Size of the underlying lattice. Supported values are 
            integers between 4 to 16. 
        
        qpu: QPU to which the graph must be made compatible.

        ratio: Desired Tx/Rx ratio.

    Returns:
        Four-tuple of transmission graph, Tx/Rx ratio, embedding, stats. 
    """
    if lattice_size not in list(range(4, 17)):
        raise ValueError("Supported lattice sizes are between 4 to 16")		

    emb, source = _create_lattice(lattice_size=lattice_size, qpu=qpu)

    network = nx.Graph()
    network.add_nodes_from(source.nodes())
    
    nx.set_node_attributes(network, 
        values={n: 1 for n in network.nodes()}, 
        name='num_transmitters')
    nx.set_node_attributes(network, values=0, name='num_receivers')
    
    num_tx = len(network)
    max_num_rx = len(set([(n[0]+x, n[1]+y) for n in network.nodes 
        for x in [-0.5,0.5] for y in [-0.5,0.5]]))
    dilution = num_tx/(max_num_rx * ratio)

    for n in list(network.nodes()):

        network.add_nodes_from(((n[0]+x, n[1]+y) 
            for x in [-0.5,0.5] for y in [-0.5,0.5]),
            num_receivers=np.random.choice([1, 0], p=[dilution, 1-dilution]),
            num_transmitters=0)
        
        network.add_edges_from((n,(n[0]+x, n[1]+y)) 
            for x in [-0.5,0.5] for y in [-0.5,0.5])

    emb = {idx: [dnx.pegasus_coordinates(16).pegasus_to_linear(n[0]), 
                dnx.pegasus_coordinates(16).pegasus_to_linear(n[1])] for 
                idx, (tx, n) in enumerate(emb.items())}

    return network, emb

def print_network_stats(network):
    """Print statistics on the network graph.

    Args:
        network: Network graph.

    Returns:
        Two-tuple of the numbers of transmitters and receivers.
    """

    num_tx, num_rx = num_tx_rx(network) 
    tx_over_rx = num_tx/num_rx
	
    print(f"Ratio of transmitters to receivers: {round(tx_over_rx, 2)}.")
    print(f"Number of transmitters is {num_tx} and receivers is {num_rx}.")
    print(f"Total nodes in the network (occupied and unoccupied) is {len(network)}.")
    print(f"Number of edges is {len(network.edges)}.")

def create_channels(network, 
    F_distribution=("binary", "real"), 
    attenuation_matrix=None):
    """
    """
    num_tx, num_rx = num_tx_rx(network)
    am = dimod.generators.mimo.lattice_to_attenuation_matrix(network)[0]

    return dimod.generators.mimo.create_channel(num_receivers=num_rx, 
        num_transmitters=num_tx, 
        F_distribution=("binary", "real"),
        attenuation_matrix=am)

def simulate_signals(channels, channel_power, transmitted_symbols=None, SNRb=float('Inf')):
    """
    """
    if not transmitted_symbols:
        num_tx = channels.shape[1]
        transmitted_symbols = np.random.choice([1, -1], size=[num_tx, 1]) 

    y, v, _, _ = dimod.generators.mimo._create_signal(channels, 
        transmitted_symbols=transmitted_symbols,
        channel_power=channel_power,
        SNRb=SNRb)

    return y, v