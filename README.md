<p align="center">
<img src="docs/img/icon-full.png" width="200">
</p>

----

Digi is an open source framework for building lightweight digital twins ("digi") and running them in a cloud-native architecture. Digis are programmable in Python, configurable via declarative API, and queryable for fast, in-situ data analytics. Digis can also be composed to form control hierarchies and to model sophisticated real-world interactions. 

One can use Digi to build _pervasive data apps_ as digis for automation, data processing, and data analytics (e.g. in IoT, smart spaces, mobile) while orchestrating these apps at an appropriate scale, from a single node machine (Raspberry Pi, laptop) to a machine cluster in cloud. Digi's runtime contains a collection of built-in "meta" digis, and one can easily extend the framework by adding new meta digis, the same way as building the apps.

Digi is designed and implemented as an extension to [Kubernetes](https://github.com/kubernetes/kubernetes) where a digi's configurations and run-time states are stored in the Kubernetes's apiserver, which one can access and manage using existing cloud-native tooling. Digi organizes data processing pipelines as _pipelets_ associated with each digi and leverages [Zed](https://github.com/brimdata/zed) to store and process the data generated/ingested by the pipelets. 

----

## Getting started
Install Digi with: `make dep` and `make install`. 

See [quickstart page](docs/quickstart.md) for more information on installation and frequently used commands.

As a hello-world example, one can use Digi to build a control hierarchy and query the digis in a smart space:
![Alt Text](https://github.com/digi-project/recording/blob/main/control_query.gif)

## Resources
Documentation:
* [Quickstart](docs/quickstart.md)
* [Development](docs/development.md)
* [Building digis](docs/build-digi.md)

More information:
* [Digibox paper](https://people.eecs.berkeley.edu/~silvery/hotnets22-digibox.pdf)
* [dSpace paper](https://people.eecs.berkeley.edu/~silvery/sosp21-dspace.pdf)
* [Example digis](https://github.com/digi-project/examples)
* [Mock digis](https://github.com/digi-project/mocks)
* [Use cases and demo](https://github.com/digi-project/demo)
