# QuickStart

## Installation

Install Kubernetes via, e.g., Docker Desktop, Minikube, or Kind.

* Required: Kubernetes CLI `[kubectl`](https://kubernetes.io/docs/tasks/tools/) and package manager `[helm 3](https://helm.sh/docs/intro/install/)` 

To validate: run `kubectl get pods` 

Set up the digi repo
* Clone the repo [https://github.com/digi-project/digi](https://github.com/digi-project/digi)
* In the repo, run `make dep` followed by `make install` .

To validate: run `digi` and you should see the available commands.


## Examples

Download example digis
* Mocks: [https://github.com/digi-project/mocks](https://github.com/digi-project/mocks)
    * This repo includes digis that simulate individual devices (i.e. mocks such as a mock lamp) and contexts (i.e. scenes such as a room). Information about how to use and configure these mocks and scenes can be found in the [digibox paper](https://drive.google.com/file/d/1LIeSiAbgEEx849h7LoQMLbm_wm08oObt/view?usp=sharing).
* Apps: [https://github.com/digi-project/examples](https://github.com/digi-project/examples)
    * Includes example apps, e.g., a lamp digivice that controls a mock lamp or a physical lamp.
* Demos (optional): [https://github.com/digi-project/demo](https://github.com/digi-project/demo)
    * Includes demos for end-to-end applications, e.g., for building monitoring.
* Recorded demos (optional): [https://github.com/digi-project/recording](https://github.com/digi-project/recording)
    * Includes pre-recorded app demos.

You can use the examples to validate digi is set up correctly: 
* Ensure Kubernetes is running: `kubectl get pods`.
* Ensure all dSpace controllers (i.e., [meta digis](TBD)) are running: `digi space start`.
* In /mocks, run `digi run lamp l1` and `digi check l1`. 

You should be able to see the lamp l1's model. See "Frequently used commands" section for additional commands you can use to interact with the digi.

## Frequently used commands
> TBD command table
