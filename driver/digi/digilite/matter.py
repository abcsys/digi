import websockets.sync.client
import json
import base64

class Cluster:
  def __init__(self, controller, cluster: int | str):
    self.controller = controller
    self.cluster = cluster

class UndefinedCluster(Cluster):
  """
  Usage:

  <controller>.cluster(<int: ClusterId>)[<int: CommandId>](payload, endpoints, debug)
  <controller>.cluster(<int: ClusterId>).read(payload, endpoints, debug)
  <controller>.cluster(<int: ClusterId>).read_event(payload, endpoints, debug)
  <controller>.cluster(<int: ClusterId>).write(payload, endpoints, debug)

  Examples:

  matter.cluster(999)[777](endpoints=2) -> chip-tool command-by-id 999 777 1 2
  matter.cluster(999).read(777, endpoints=2) -> chip-tool read-by-id 999 777 1 2
  matter.cluster(999)[777]("payload", endpoints=2) -> chip-tool command-by-id 999 777 payload 1 2
  """

  def raw_invoke(self, cmd: str, payload, endpoints: list[str | int] | str | int, debug: bool):
    endpoints = endpoints if type(endpoints) == list else [endpoints]
    endpoints = map(lambda e: str(e), endpoints)
    endpoints = ','.join(endpoints)
    return self.controller.raw_invoke(f"any {cmd.replace('_', '-')} {self.cluster} {payload} {self.controller.node_id} {endpoints}", debug=debug)

  def __getattr__(self, cmd):
      def dynamic_method(payload: str = "", endpoints: list[str | int] | str | int = "0xFFFF", debug=False):
        nonlocal cmd
        if type(cmd) != str:
          payload = f"{cmd} payload"
          cmd = "command_by_id"
        
        aliases = {
          "read": "read-by-id",
          "read_event": "read-event-by-id",
          "write": "write-by-id"
        }

        if cmd in aliases:
          cmd = aliases[cmd]

        return self.raw_invoke(cmd, payload=payload, endpoints=endpoints, debug=debug)
      return dynamic_method

class DefinedCluster(Cluster):
  """
  Usage:

  <controller>.cluster(<str: ClusterName>).<str: CommandName>(payload, endpoints, debug)
  Examples:

  matter.cluster("onoff").on(endpoints=2) -> chip-tool onoff on 1 2
  matter.cluster("onoff").off(endpoints=2) -> chip-tool onoff off 1 2
  matter.cluster("onoff").read("on-off", endpoints=2) -> chip-tool onoff read on 1 2
  """

  def raw_invoke(self, cmd: str, payload, endpoints: list[str | int] | str | int, debug: bool):
    endpoints = endpoints if type(endpoints) == list else [endpoints]
    endpoints = map(lambda e: str(e), endpoints)
    endpoints = ','.join(endpoints)
    return self.controller.raw_invoke(f"{self.cluster} {cmd.replace('_', '-')} {payload} {self.controller.node_id} {endpoints}", debug=debug)

  def __getattr__(self, cmd: str):
      def dynamic_method(payload: str = "", endpoints: list[str | int] | str | int = "0xFFFF", debug=False):
        return self.raw_invoke(cmd, payload=payload, endpoints=endpoints, debug=debug)
      return dynamic_method

class Controller:
  """
  Matter controller wrapper over chip-tool
  """

  def __init__(self):
    """
    Connects to the interactive server by chip-tool using websockets
    """
    self.ws_client = websockets.sync.client.connect("ws://localhost:9002")
    self.node_id = 1
  
  def raw_invoke(self, cmd: str, debug=False) -> object:
    """
    Sends a command to chip-tool and waits for response

    Parameters:
    - cmd: Command to send to chip-tool
    - debug: Enable debugging mode - { result, logs } vs result

    Returns:
    Array of results OR { result: [object], logs: [object] }
    """
    self.ws_client.send(cmd)
    recv = self.ws_client.recv()
    res = json.loads(recv)
    for log in res["logs"]:
      log["message"] = base64.b64decode(log["message"]).decode('utf-8')
    
    if len(res["results"]) > 0 and "error" in res["results"][0]:
      raise Exception(res["logs"])

    if not debug:
      res = res["results"]
    return res

  def pair(self, code: str, debug=False):
    """
    Pair with a matter device using a setup code

    Parameters:
    - code: Code outputted when pairing with a matter device
    """
    return self.raw_invoke(f"pairing code {self.node_id} {code} --bypass-attestation-verifier 1", debug=debug)

  def cluster(self, cluster: int | str):
    """
    Return a cluster object. Invoking commands, reading, and writing involves the cluster

    Parameters
    - cluster: An integer for the cluster if it is not known and a string if it is known

    Returns:
    DefinedCluster or UndefinedCluster
    """
    if type(cluster) == str:
      return DefinedCluster(self, cluster)
    else:
      return UndefinedCluster(self, cluster)

  def detach(self):
    """
    Detach from the websocket connection
    """
    self.ws_client.close()