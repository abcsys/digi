# Digi Developer Documentation

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development](#development)
3. [More](#more)


## Getting Started
### System Setup
1. **Kubernetes**
    * You're free to use any flavor of Kubernetes: Minkube, Kind, etc. However, we officially support [Docker Desktop](https://www.docker.com/products/docker-desktop/) only. Meaning, you might have to do additional work to get things working.
    * :warning: Minikube `^1.28.0` is known to have issues with port forwarding. Proceed at your own risk.
2. **Kubernetes Tools**
    * Kubernetes CLI [(kubectl)](https://kubernetes.io/docs/tasks/tools/) 
    * Kubernetes Package Manager [(helm)](https://helm.sh/docs/intro/install/)
    * To make sure everything is working correctly thus far, run `kubectl get pods`.
    * The proceeding instructions assumes you have a running Kubernetes instance and have installed the `kubectl` and `helm`.
3. **Digi**
    * Clone the repository [https://github.com/digi-project/digi](https://github.com/digi-project/digi). **Note**, if you're planning on making changes, please checkout [Workflow](#workflow)
    * Run the follwing commands:
        ```sh
        make dep && make digi
        digi
        ```
    * You should see a list of command provided by digi.

4. Take a look at [Quickstart](quickstart.md#Examples) for more details on how to create, configure and deploy a digi to your Kubernetes cluster.


## Development
### Workflow
1. Make your own [**fork**](https://github.com/digi-project/digi/fork) of the project.
2. Add upstream to list of remotes or alternatively use the Sync Fork feature on github. Make sure your fork is up to date before every commit. 
3. Work on your code. Add feature, add tests, add documentation, remove bugs.
4. [Commit](development.md#commit) code Push your code to **your fork**, not digi. 
5. Go to GitHub and open a [pull request](https://github.com/digi-project/digi/compare)
6. Pass all CI test (not implemented yet...)
7. Add the appropriate reviewer for you pull request and ping them on Slack.

Please read [Forking & Pull Requests](https://gist.github.com/Chaser324/ce0505fbed06b947d962) for a general overview of how forking and pull requests works. Additionally, ensure that your commit and pull request messages abide by our [guidelines](developement.md). 


## More
* [Quickstart](quickstart.md)
* [Digi Design](design.md)
* [Example Digis](https://github.com/digi-project/mocks)
* [Use Cases and Demo](https://github.com/digi-project/demo)
 