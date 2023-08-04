[![Open in Leap IDE](
  https://cdn-assets.cloud.dwavesys.com/shared/latest/badges/leapide.svg)](
  https://ide.dwavesys.io/#https://github.com/dwave-examples/cooperative-multipoint)

# Decoding Cellphone Signals

In radio networks, such as those used by cellphones, 
[MIMO](https://en.wikipedia.org/wiki/MIMO) is a method of increasing link 
capacity by using multiple transmission and receiving antennas to exploit 
[multipath propagation](https://en.wikipedia.org/wiki/Multipath_propagation). 

In [coordinated multipoint (CoMP)](https://en.wikipedia.org/wiki/Cooperative_MIMO)
neighboring cellular base stations coordinate transmissions and jointly process 
received signals.

Such techniques enable network providers to increase and improve their cellphone
service, especially in dense urban areas. However, such techniques demand 
processing capacity that can increase steeply with network size. 

This notebook demonstrates the use of quantum computer in decoding transmissions 
in CoMP problems and compares performance to other decoding
methods in use by contemporary cellular networks. 

## Installation

You can run this example
[in the Leap IDE](https://ide.dwavesys.io/#https://github.com/dwave-examples/cooperative-multipoint).

Alternatively, install requirements locally (ideally, in a virtual environment):

    pip install -r requirements.txt

## Usage

To run the notebook:

```bash
jupyter notebook
```

[^1]: Leap's IDE, which runs VS Code, does not support all notebook extensions. 

## Problem Formulation

MIMO requires effective and efficient demultiplexing of mutually-interfering 
transmissions. Contemporary base stations use linear filters such as 
[zero forcing](https://en.wikipedia.org/wiki/Zero-forcing_precoding) and 
[minimum mean squared error (MMSE)](https://en.wikipedia.org/wiki/Minimum_mean_square_error). 
However, these methods perform poorly when the ratio of cellphones to base stations 
increase.[[1]](#1) More advanced decoding techniques improve throughput but demand 
computational resources that grow exponentially with network size.

PLACEHOLDER TEXT:

The transmission received by a base station, comprising symbols sent in a
single time period from all cellphones within range, is given by,

![eq1](_static/eq_y_func_s_n.png)

where the left side is the received signal and the right side is the wireless
channel acting on a vector of transmitted 
[QAM](https://en.wikipedia.org/wiki/Quadrature_amplitude_modulation) signals plus
a vector representing the channel's noise.

[[2]](#2) formulates the transmission-decoding problem as a QUBO and you can 
see Ocean software's implementation in 
[dimod](https://docs.ocean.dwavesys.com/en/stable/docs_dimod/sdk_index.html).

In brief, the decoding problem is represented as a maximum likelihood,

![eq2](_static/eq_max_likelihood.png)

where for BPSK,

![eq3](_static/eq_bpsk_qubo.png)


### References

<a name="1">[1]</a> Toshiyuki Tanaka. 
A Statistical-Mechanics Approach to Large-System Analysis of CDMA Multiuser Detectors.
IEEE TRANSACTIONS ON INFORMATION THEORY, VOL. 48, NO. 11, NOVEMBER 2002

<a name="2">[2]</a> Minsung Kim, Davide Venturelli, and Kyle Jamieson. 
Leveraging quantum annealing for large MIMO processing in centralized radio access networks.
SIGCOMM '19: Proceedings of the ACM Special Interest Group on Data Communication, August 2019, Pages 241–255 
https://dl.acm.org/doi/10.1145/3341302.3342072

## License

See [LICENSE](LICENSE.md) file.
