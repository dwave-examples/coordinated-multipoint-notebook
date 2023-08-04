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

## License

See [LICENSE](LICENSE.md) file.
