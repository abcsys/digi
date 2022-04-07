**dSpace makes it easy to build simple, declarative, and composable abstractions in smart spaces.**

NOTE: this is an outdated guide; updates are forthcoming

Define a digi schema:

```yaml
group: digi.dev
version: v1
kind: Plug
control:
  power: string
```

Program the digi's driver:

```yaml
from digi import on
# tuya device library
import pytuya
plug = pytuya.Plug("DEVICE_ID")
@on.control("power")
def h(power):
    plug.set(power["intent"])
```

Build and run the digi:

```bash
dq build plug; dq run plug plut-test
```

Update the intent of the digi in the model's yaml file (e.g., cr.yaml)

```yaml
apiVersion: digi.dev/v1
kind: Plug        
metadata:
  name: plug-test
spec:
  control:        
    power:
      # 'I want the plug switched off'
      intent: "off"
```

Apply it via kubectl: `kubectl apply -f cr.yaml` 

Install dSpace's driver library: `pip install digi`. The command line dSpace manager: `go get -u digi.dev/dq`. Or build `dq` from the source from this repo: `make dq`.


## Concepts

**Digi:** The basic building block in dSpace is called *digi*. Each digi has a *model* and a *driver*. A model consists of attribute-value pairs organized in a document (JSON) following a predefined *schema*. The model describes the desired and the current states of the digi; and the goal of the digi's driver is to take actions that reconcile the current states to the desired states.

**Programming driver:** Each digi's driver can only access its own model (think of it as the digi's "world view"). Programming a digi is conceptually very simple - manipulating the digi's model/world view (essentially a JSON document) plus any other actions to affect the external world (e.g., send a signal to a physical plug, invoke a web API, send a text messages to your phone etc.). The dSpace's runtime will handle the rest, e.g., syncing states between digis' world views when they are composed.

Example `Room` digivice:
```python
from digi import on
from digi.view import TypeView, DotView
# invoked upon mount or control attributes changes
@on.mount
@on.control
def handle_brightness(model):  
    # chained transformation of model
    with TypeView(model) as tv, DotView(tv) as dv: 
      
        # control attribute for room brightness 
        rb = dv.room.control.brightness        
        
        # if no lamps brightness status set to 0
        rb.status = 0
        if "lamps" not in dv:
            return
          
        # count active lamps
        active_lamps = [l for _, l in dv.lamps.items() 
                    if l.control.power.status == "on"]
        
        # iterate and set active lamp brightness
        for lamp in active_lamps:
            # room brightness is the sum of all lamps
            room_brightness.status += \
            lamp.control.brightness.status 
            
            # divide intended brightness across lamps
            lamp.control.brightness.intent = \
            room_brightness.intent / len(active_lamps)
            
    # At the closing of the "with" clause, changes on 
    # DotView will be applied to the TypeView and then 
    # to the model.
if __name__ == '__main__':
    digi.run()
```

**Build and run:** After defining the digi's schema and programing its driver, developers can build a *digi image* and push it to a digi repository for distributiton. Users can then pull the digi image, run it on dSpace, and interact with the digi by updating its model, e.g., specifies its desired states.

**Digivice:** In this tutorial, we will focus on a special type of digi called *digivice* (e.g., the Plug in Quick Start). A digivice model has control attributes (e.g., `control.power` in Plug) where each control attribute has an intent field (tracking the desired states) and a status field (tracking the current states).

> TBD digilake
Digivices can be composed via the *mount* operator, forming digivice hierarchies. Mounting a digi A to another digi B will allow B to change the intent fields and read the status fields of A (via updating the corresponding attribute replica of A in B's own model).

Example digi-graph:


## Using Dq

```bash
$ dq
Command-line dSpace manager.
Usage:
  dq [command]
Available Commands:
  alias       Create a digi alias
  build       Build a digi image
  help        Help about any command
  image       List available digi images
  log         Print log of a digi driver
  mount       Mount a digivice to another digivice
  pipe        Pipe a digilake's input.x to another's output.y
  pull        Pull a digi image
  push        Push a digi image
  rmi         Remove a digi image
  run         Run a digi given kind and name
  stop        Stop a digi given kind and name
Flags:
  -h, --help    help for dq
  -q, --quiet   Hide output
Use "dq [command] --help" for more information about a command.
```
