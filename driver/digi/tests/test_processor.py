import time
import yaml
import os
import sys
import pprint as pp

_dir = os.path.dirname(os.path.realpath(__file__))
_parent_dir = os.path.dirname(_dir)
sys.path.insert(0, _parent_dir)

from digi.processor import jq

test_yaml = f"""
control:
  brightness:
    intent: 0.8
    status: 0
  mode:
    intent: sleep
    status: sleep
mount:
  mock.digi.dev/v1/lamps:
    default/lamp-test:
      spec:
        control:
          power: 
            intent: "on"
  mock.digi.dev/v1/motionsensors:
    default/motionsensor-test:
      spec:
        obs:
          last_triggered_time: {time.time()}
reflex:
  motion-mode:
    policy: 'if $time - ."motionsensor-test".obs.last_triggered_time <= 600 
             then .root.control.mode.intent = "work" else . end'
    priority: 1
"""

if __name__ == '__main__':
    v = yaml.load(test_yaml, Loader=yaml.FullLoader)
    start = time.time()
    jq(v["reflex"]["motion-mode"]["policy"])(v)
    print(f"took {time.time() - start}s")
    pp.pprint(v)
