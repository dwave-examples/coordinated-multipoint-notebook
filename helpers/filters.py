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

def create_filter(channel_matrix, method, snr_over_nt=float('inf')):
    """
    """
    if method not in ['zero_forcing', 'matched_filter', 'MMSE']:
        raise ValueError(f"filter {method} is not supported")
    return dimod.generators.mimo.linear_filter(channel_matrix, method=method, SNRoverNt=snr_over_nt)

def apply_filter(filter, signal):
    """
    """
    v = np.sign(np.real(np.matmul(filter, signal)))[:,0]
    
    # Randomly set unconnected-transmitter symbols
    mask = v==0
    v[mask] = np.random.choice([-1, 1], size=v.shape)[mask] 
    return v