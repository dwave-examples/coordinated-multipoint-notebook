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

def _create_lattice(lattice_size=16, target=None):
    """Create a lattice with an embedding

    Args:
        lattice_size: Size of the lattice. 

    Returns:
        Two tuple of embedding and the source lattice. 
    """
    if not target:
        nodes_lattice_size = [dnx.pegasus_coordinates(16).nice_to_linear(node) 
            for node in dnx.pegasus_graph(m=16, nice_coordinates=True).nodes 
            if node[1]<lattice_size and node[2]<lattice_size]
        qpu_graph = dnx.pegasus_graph(m=16, node_list=nodes_lattice_size)	
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
         
    props = dict(scale=scale, 
                    node_defects=node_defects, 
                    edge_defects=edge_defects, 
                    nodes=source.number_of_nodes(), 
                    edges=source.number_of_edges())

    return emb, source, props


def configure_network(lattice_size=16, target=None, ratio=1):
    """Configure network transmitters and receivers.

    Args:
        lattice_size: Size of the underlying lattice.
        
        target: QPU.

        ratio: TBD change to tx/rx ratio

    Returns:
        Four-tuple of transmission graph, Tx/Rx ratio, embedding, stats. 
    """		

    emb, source, props = _create_lattice(lattice_size=lattice_size, target=None)

    transmission_graph = nx.Graph()
    transmission_graph.add_nodes_from(source.nodes())
    
    nx.set_node_attributes(transmission_graph, 
        values={n: 1 for n in transmission_graph.nodes()}, 
        name='num_transmitters')
    nx.set_node_attributes(transmission_graph, values=0, name='num_receivers')
    
    for n in list(transmission_graph.nodes()):

        transmission_graph.add_nodes_from(((n[0]+x, n[1]+y) 
            for x in [-0.5,0.5] for y in [-0.5,0.5]),
            num_receivers=np.random.choice([1, 0], p=[ratio, 1-ratio]),
            num_transmitters=0)
        
        transmission_graph.add_edges_from((n,(n[0]+x, n[1]+y)) 
            for x in [-0.5,0.5] for y in [-0.5,0.5])

    # nx.set_node_attributes(transmission_graph, values={n: 0 if n in variables else random.choice([*[1]*20, *[0]*dilution]) for n in transmission_graph.nodes()}, name='num_receivers')
	
    num_tx = sum(nx.get_node_attributes(transmission_graph, 
        "num_transmitters").values())
    num_rx = sum(nx.get_node_attributes(transmission_graph, 
        "num_receivers").values())
    tx_over_rx = num_tx/num_rx
	
    return transmission_graph, tx_over_rx, emb, props
