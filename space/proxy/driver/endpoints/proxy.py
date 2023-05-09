from flask import Blueprint, request
from kubernetes import client
from kubernetes.stream import stream

proxy = Blueprint("proxy", __name__, url_prefix="/proxy")

@proxy.route("/list", methods=["GET"])
def list_digis():
    """
    List digis running in dspace
    """
    v1 = client.CoreV1Api()
    ret = v1.list_service_for_all_namespaces()
    digis = []
    for item in ret.items:
        if item.metadata.namespace == "default" and item.metadata.name not in ["lake", "proxy"]:
            digis.append(item.metadata.name)
    return digis, 200
    
@proxy.route("/query", methods=["GET"])
def query():
    """
    Query digi
    """
    digi = request.json.get("digi")
    egress = request.json.get("egress")
    query = request.json.get("query")
    v1 = client.CoreV1Api()
    pod_ret = v1.list_pod_for_all_namespaces()

    # find lake pod
    print("Searching for lake pod...")
    lake_found = False
    for item in pod_ret.items:
        if item.metadata.namespace == "default" and \
                "lake" in item.metadata.name and \
                item.status.phase == "Running":
            lake_pod = item.metadata.name
            lake_found = True
            break

    # return error (temporarily unavailable)
    if not lake_found:
        return "Lake not found (temporarily unavailable)\n", 500
    
    # submit zed query to lake pod
    zed_query = ""
    if digi:
        if egress:
            zed_query += f"from {digi}@{egress}"
        else:
            zed_query += f"from {digi}"
    zed_query += " | not __meta"
    if query:
        zed_query += f" | {query}"
    query_cmd = [
        "/bin/sh",
        "-c",
        f"zed query '{zed_query}'"
    ]
    query_ret = stream(v1.connect_get_namespaced_pod_exec, name=lake_pod, namespace="default",
        command=query_cmd,
        stderr=False,
        stdout=True,
        stdin=True,
        tty=True
    )
    return query_ret, 200

@proxy.route("/check", methods=["GET"])
def check():
    """
    Check digi
    """
    digi = request.json.get("digi")
    v1 = client.CoreV1Api()
    pod_ret = v1.list_pod_for_all_namespaces()
    for item in pod_ret.items:
        if item.metadata.name == digi:
            return item.spec, 200
    return "Digi not found\n", 404
