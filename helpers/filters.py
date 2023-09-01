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
import time
import dimod

from helpers.network import configure_network, create_channels, _num_tx_rx
from helpers.draw import draw_instantiation_times

ALL_METHODS = ['zero_forcing', 'matched_filter', 'MMSE']

def create_filters(channels: np.ndarray, 
                   methods: list = None, 
                   snr_over_nt: float = float('inf')) -> dict:
    """Instantiate linear filters.

    Args:
        channels: Transmission channels.

        methods: Types of filter. Supported values are:

            * 'matched_filter': Matched filter.
            * 'MMSE': Minimum mean square error filter.
            * 'zero_forcing': Zero forcing filter.

        snr_over_nt: Signal-to-noise ratio.

    Returns:
        Instantiated filters.
    """
    if not methods:
        methods = ALL_METHODS
    elif unknown := set(methods).difference(ALL_METHODS):
        raise ValueError(f"filter {unknown} not supported")
    
    return {f'filter_{method}': dimod.generators.mimo.linear_filter(
        channels, method=method, SNRoverNt=snr_over_nt) for method in methods}

def apply_filters(signal: np.ndarray, filters: dict) -> dict:
    """Decode a transmission with the given filters.

    Args:
        signal: Received sequence of symbols, possibly noisy.
        
        filters: Linear filters used to decode the transmission.

    Returns:
        Dict of signals decoded with each of the given filters.
    """
   
    return {name: np.sign(np.real(np.matmul(filter, signal)))[:,0] for 
        name, filter in filters.items()}

def compare_signals(v: np.ndarray, 
                    transmission: np.ndarray, 
                    silent_return: bool = False) -> float:
    """Compare two sequences of transmission symbols.

    Args:
        v: A sequence of transmission symbols.

        transmission: A sequence of transmission symbols.

        silent_return: Boolean flag indicating whether to print results.

    Returns:
        Percentage of the sequence with identical symbols (returned if `silent_return=True`).  
    """
    if isinstance(v, dict):
        success_rate = {filter: sum(v[filter].flatten() == transmission.flatten()) 
            for filter in v.keys()}
        success_rate = {name: round(100*val/len(transmission)) for 
            name, val in success_rate.items()}

        if not silent_return:
            for name in success_rate.keys():
                print(f"{name}: decoded with a success rate of {success_rate[name]}%.")
        else:
            return success_rate
    else:
        if isinstance(v, dimod.SampleSet):
            received = np.array(list(v.first.sample.values()))
        elif isinstance(v, np.ndarray):
            received = v.flatten()
        else:
            raise ValueError("Unknown signal type")
        
        sr = round(100*sum(received == transmission.flatten())/len(transmission))
        if not silent_return:
            print(f"Decoded with a success rate of {sr}%.")
        else:
            return sr
    
def time_filter_instantiation(network_sizes: list, methods: list = None):
    """Measure the instantiation time of filters.

    Args:
        network_sizes: Sizes of the underlying lattice, :math:`3*(network_size - 1)`.

        methods: Types of filter. Supported values are:

            * 'matched_filter': Matched filter.
            * 'MMSE': Minimum mean square error filter.
            * 'zero_forcing': Zero forcing filter.
    """
    if not methods:
        methods = ALL_METHODS

    times = {key: [] for key in methods}
    for ns in network_sizes:

        network, _ = configure_network(network_size=ns)
        channels, _ = create_channels(network)

        num_tx, num_rx = _num_tx_rx(network)
        print(f"\nFor a network of {num_tx} cellphones and {num_rx} base stations:\n")

        for method in methods:
            start_t = time.time_ns()
            create_filters(channels, methods=[method])
            time_ms = (time.time_ns() - start_t)/1000000
            times[method].append(time_ms)
            if time_ms < 500:
                print(f"\t* {method} took about {round(time_ms)} milliseconds.")
            else:
                print(f"\t* {method} took about \x1b[31m {round(time_ms)} \x1b[0m  milliseconds.")

    draw_instantiation_times(times, network_sizes)