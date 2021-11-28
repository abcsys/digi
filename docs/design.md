# Digi design

  * [Model](#model)
    + [Initialization](#initialization)
  * [Driver](#driver)
  * [Data pool](#data-pool)
  * [Operations](#operations)

Digi is a framework for creating a minimalistic yet versatile digital representation (a "digi") for any physical or cyber object(s) that is programmable, trainable, queryable, and reusable; it can make decisions and take actions.

Each digi has a model, a data pool, and a driver. The model contains attribute-values that follow a predefined schema. The data pool stores any data related to the digi where the data in the pool can be updated and queried efficiently. The driver is a piece of code that read/writes from the model and takes actions including dumping data to the data pool and querying the data pool. 

> Control abstraction and data abstraction.

## Digi semantics

### Model

#### Schema 
#### Register 

### Data Pool
> Ephemeral data

#### Ingest
#### Query

### Driver
### Development 
> dq

#### Create
#### Build
#### Run
> Any k8s

#### Distribute
> Hub for digi images

### Runtime

The above design doesn't restrict how a digi is implemented, e.g., one can use Postgres, TimescaleDB, or a cloud-hosted data lake (e.g. Databricks) for the pool and Nodejs or Spring for driver and model. The digi library in this repo provides an implementation based on the *right* toolstacks.

#### Model: Kubernetes CR
#### Driver: Kubernetes Controller
#### Data pool: Zed

> TBD one can view a digi as a microservice backed by a data lake.
> TBD over-the-cloud-vertical integration

## Examples

> TBD car, lamp, temperature sensor, human, home

## Related topics

> In-situ processing
> Object-oriented databases
> Personal Information Management (PIM)

## Current Status



