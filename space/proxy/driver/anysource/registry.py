from anysource import datahub
import digi

from kubernetes import client
import requests
import json
import threading

def register_dspace(registry_endpoint, user_name, dspace_name):
    kube_client = client.CoreV1Api()

    proxy_service = kube_client.read_namespaced_service(digi.name, "default")
    proxy_endpoint = proxy_service.spec.cluster_ip

    # TODO: use external endpoint
    # external_endpoints = proxy_service.spec.external_i_ps
    digi.logger.info(f"Registering {user_name}/{dspace_name} at {registry_endpoint}.")
    res = requests.put(registry_endpoint, 
        headers={
            # TODO: add auth token (from login) to header
        },
        json={
            "user_name": user_name,
            "dspace_name": dspace_name,
            "overwrite": True,
            "proxy_endpoint": proxy_endpoint
    })
    if res.status_code == 200:
        data = json.loads(res.text)
        datahub_endpoint = data.get("datahub_endpoint")
        datahub_group = data.get("datahub_group")
        digi.logger.info(f"Datahub-proxy comms: endpoint={datahub_endpoint} id={datahub_group}")
        datahub_thread = threading.Thread(target=datahub.emit_digi_data_forever,
                                          args=(datahub_endpoint, datahub_group))
        datahub_thread.start()
    else:
        digi.logger.info(f"Failed to register digi with registry:")
        digi.logger.info(res.content)
        