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

def draw_network(network):
    fig = plt.figure(figsize=(8, 3))
    tx = nx.get_node_attributes(network, 'num_transmitters')
    rx = nx.get_node_attributes(network, 'num_receivers')
    nx.draw_networkx(network, pos={n: n for n in network.nodes()}, 
        node_color = ['r' if tx[n] else 'g' if rx[n] else 'w' for n in network.nodes()], 
        with_labels=False, node_size=50)
    plt.show()