from datahub.emitter.mcp import MetadataChangeProposalWrapper
import datahub.emitter.mce_builder as builder
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import ChangeTypeClass, DatasetPropertiesClass
from kubernetes import client

import digi
import time
import ast

def get_emitter(endpoint):
    # Create an emitter to DataHub over REST
    emitter = DatahubRestEmitter(endpoint, extra_headers={})

    # Test the connection
    emitter.test_connection()

    return emitter

def emit_metadata_event(emitter, id, dataset, data):
    # Construct a MetadataChangeProposalWrapper for a custom entity
    # dataset_urn = f"urn:li:customEntity:{id}:{dataset}"
    dataset_urn = builder.make_dataset_urn(id, dataset)
    dataset_name = f"{dataset}"
    dataset_description = f"{dataset}:{id} fields={list(data.keys())}"
    dataset_properties = DatasetPropertiesClass(
        name=dataset_name,
        description=dataset_description,
        customProperties=data
    )

    mcp = MetadataChangeProposalWrapper(
        entityUrn=dataset_urn,
        aspect=dataset_properties
    )

    # Write the metadata change proposal to DataHub
    print(f"Emitting dataset {id}:{dataset}")
    emitter.emit(mcp)

# emit digi metadata forever
def emit_digi_data_forever(datahub_endpoint, datahub_group):
    emitter = get_emitter(datahub_endpoint)

    prev_state = {
        "digis": set(),
        "mounts": set()
    }
    
    while True:
        # Create an instance of the API class
        api_instance = client.CustomObjectsApi()
        group = "anysource.io"
        version = "v1"
        try:
            api_response = api_instance.get_api_resources(group, version)
            digis = []
            for resource in api_response.resources:
                resource_digis = api_instance.list_cluster_custom_object(group, version, resource.name)
                for resource_digi in resource_digis["items"]:
                    digi_config = ast.literal_eval(resource_digi["metadata"]["annotations"]["kubectl.kubernetes.io/last-applied-configuration"])
                    digis.append(digi_config)
            
            for d in digis:
                digi.logger.info(str(d))
                digi.logger.info(type(d))
                data = {
                    "name": d["metadata"]["name"],
                    "kind": d["kind"]
                }
                emit_metadata_event(emitter, datahub_group, d["metadata"]["name"], data)
        except Exception as e:
            digi.logger.info("Failed to write dspace data to Datahub: ")
            digi.logger.info(e)

        time.sleep(10)
