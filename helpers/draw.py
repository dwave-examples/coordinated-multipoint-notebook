# Copyright 2023 D-Wave
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

# Colors are from the Okabe-Ito palette, which remains distinguishable under
# the common forms of color-vision deficiency. Every series also has a distinct
# marker so that meaning is never carried by color alone.
styles = {
    "QPU": {"color": "#0072B2", "marker": "*"},  # blue, star
    "zero_forcing": {"color": "#009E73", "marker": "^"},  # green, up triangle
    "MMSE": {"color": "#CC79A7", "marker": "v"},  # pink, down triangle
    "matched_filter": {"color": "#E69F00", "marker": ">"},  # orange, right triangle
    "SA": {"color": "#D55E00", "marker": "x"},  # vermillion, cross
    "greedy": {"color": "#56B4E9", "marker": "p"},  # sky blue, pentagon
    "tabu": {"color": "#000000", "marker": "D"},  # black, diamond
}

# Network node appearance: transmitters and receivers differ in shape and color.
NODE_STYLES = {
    "transmitter": {
        "color": "#E69F00",
        "shape": "s",
        "size": 50,
        "label": "Transmitter (cellphone)",
    },
    "receiver": {"color": "#0072B2", "shape": "o", "size": 50, "label": "Receiver (base station)"},
    "off": {"color": "white", "shape": "o", "size": 20, "label": "Turned-off base station"},
}


def draw_network(network: nx.Graph):
    """Plot the given network.

    Transmitters are drawn as orange squares, receivers as blue circles, and
    turned-off base stations as small hollow grey circles. A legend identifies
    each node type.

    Args:
        network: Network graph.
    """
    if len(network) < 1000:
        fig = plt.figure(figsize=(8, 3))
    else:
        fig = plt.figure(figsize=(10, 10))

    tx = nx.get_node_attributes(network, "num_transmitters")
    rx = nx.get_node_attributes(network, "num_receivers")

    groups = {
        "transmitter": [n for n in network.nodes() if tx[n]],
        "receiver": [n for n in network.nodes() if not tx[n] and rx[n]],
        "off": [n for n in network.nodes() if not tx[n] and not rx[n]],
    }
    pos = {n: n for n in network.nodes()}

    # Color edges by what they join: orange for the transmitter lattice, blue
    # for transmitter-to-receiver channels, grey for anything touching a
    # turned-off node. This matches the static diagram in the notebook.
    def _edge_color(u, v):
        if tx[u] and tx[v]:
            return NODE_STYLES["transmitter"]["color"]
        if (tx[u] or tx[v]) and (rx[u] or rx[v]):
            return NODE_STYLES["receiver"]["color"]
        return "#BBBBBB"

    nx.draw_networkx_edges(
        network, pos=pos, edge_color=[_edge_color(u, v) for u, v in network.edges()], width=0.8
    )
    for kind, nodes in groups.items():
        if not nodes:
            continue
        style = NODE_STYLES[kind]
        nx.draw_networkx_nodes(
            network,
            pos=pos,
            nodelist=nodes,
            node_color=style["color"],
            node_shape=style["shape"],
            node_size=style["size"],
            edgecolors="#555555",
            linewidths=0.8,
            label=style["label"],
        )

    plt.legend(loc="upper left", bbox_to_anchor=(1.01, 1), scatterpoints=1)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def draw_loop_comparison(
    results: dict, network_size: int = 16, ratio: float = 1.5, SNRb: float = 5
):
    """Plot results of decoding comparisons.

    Each solver is drawn with its own marker and color, and its mean is drawn
    as a horizontal line in the same color.

    Args:
        results: results returned from other helper functions.
        network_size: Size of the network's underlying lattice.
        ratio: Ratio of transmitters to receivers.
        SNRb: Signal-to-noise ratio.
    """
    fig = plt.figure(figsize=(8, 3))

    for key in results:
        style = styles[key]
        plt.plot(
            results[key],
            linestyle="none",
            marker=style["marker"],
            color=style["color"],
            label=key,
            markersize=6,
        )
        plt.plot(len(results[key]) * [np.mean(results[key])], color=style["color"], linewidth=1)

    plt.xlabel("Run")
    plt.ylabel("Success Rate [%]")
    plt.legend(loc="upper left", bbox_to_anchor=(1.01, 1))
    plt.grid(alpha=0.3)
    plt.xticks(range(len(results[key])))  # All results are the same length (runs)
    plt.suptitle(f"Network size={network_size}, Tx/Rx$\\approx${ratio}, SNRb={SNRb}")
    plt.show()


def draw_instantiation_times(times: dict, network_sizes: dict):
    """Plot filter instantiation times for a range of network sizes.

    Args:
        times: Instantiations times, as a dict.
        network_sizes: Sizes of the underlying lattice.
    """

    fig = plt.figure(figsize=(8, 3))

    for key in times:
        style = styles[key]
        plt.plot(
            times[key],
            linestyle="-",
            marker=style["marker"],
            color=style["color"],
            label=key,
            markersize=6,
        )

    plt.xlabel("Network Size")
    plt.ylabel("Instantiation Time [ms]")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.xticks(range(len(times[key])), labels=network_sizes)
    plt.suptitle(f"Instantiation Times for Standard Linear Filters")
    plt.show()
