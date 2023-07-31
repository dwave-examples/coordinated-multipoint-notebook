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

from helpers.network import configure_network, create_channels, num_tx_rx

ALL_METHODS = ['zero_forcing', 'matched_filter', 'MMSE']

def create_filter(channel_matrix, method, snr_over_nt=float('inf')):
    """
    """
    if method not in ALL_METHODS:
        raise ValueError(f"filter {method} is not supported")
    return dimod.generators.mimo.linear_filter(channel_matrix, method=method, SNRoverNt=snr_over_nt)

def create_filters(channels, methods=None, snr_over_nt=float('inf')):
    """
    """
    if not methods:
        methods = ALL_METHODS
    return {f'filter_{method}': create_filter(channels, 
            method=method, 
            snr_over_nt=snr_over_nt) 
        for method in methods}

def apply_filter(filter, signal):
    """
    """
    v = np.sign(np.real(np.matmul(filter, signal)))[:,0]
    
    # Randomly set unconnected-transmitter symbols
    mask = v==0
    v[mask] = np.random.choice([-1, 1], size=v.shape)[mask] 
    return v

def apply_filters(signal, filters):
    """
    """
   
    return {name: apply_filter(filter, signal) for name, filter in filters.items()}

def compare_signals(v, transmission):
    """
    """
    if isinstance(v, dict):
        success_rate = {filter: sum(v[filter].flatten() == transmission.flatten()) 
            for filter in v.keys()}
        success_rate = {name: round(100*val/len(transmission)) for 
            name, val in success_rate.items()}

        for name in success_rate.keys():
            print(f"{name}: decoded with a success rate of {success_rate[name]}%.")
    else:
        if isinstance(v, dimod.SampleSet):
            received = np.array(list(v.first.sample.values()))
        elif isinstance(v, np.ndarray):
            received = v.flatten()
        else:
            raise ValueError("Unknown signal type")
        
        sr = round(100*sum(received == transmission.flatten())/len(transmission))
        print(f"Decoded with a success rate of {sr}%.")
    
def time_filter_instantiation(network_size, methods=None):
    """
    """
    if not methods:
        methods = ALL_METHODS

    for lattice_size in network_size:

        network, _ = configure_network(lattice_size=lattice_size)
        channels, cp = create_channels(network)

        num_tx, num_rx = num_tx_rx(network)
        print(f"\nFor a network of {num_tx} cellphones and {num_rx} base stations:\n")

        for method in methods:
            start_t = time.time_ns()
            create_filter(channels, method=method)
            time_ms = (time.time_ns() - start_t)/1000000
            print(f"\t* {method} took about {round(time_ms)} milliseconds.")
