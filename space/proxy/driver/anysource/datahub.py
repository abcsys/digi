from datahub.emitter.mcp import MetadataChangeProposalWrapper
import datahub.emitter.mce_builder as builder
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import ChangeTypeClass, DatasetPropertiesClass
from kubernetes import client

import digi
import time
import re

def get_emitter(endpoint):
    # Create an emitter to DataHub over REST
    emitter = DatahubRestEmitter(endpoint, extra_headers={})

    # Test the connection
    emitter.test_connection()

    return emitter

def emit_new_digi_mcp(emitter, group, dataset, data):
    # Construct a MetadataChangeProposalWrapper for a custom entity
    dataset_urn = builder.make_dataset_urn(group, dataset)
    dataset_name = f"{dataset}"
    dataset_properties = DatasetPropertiesClass(
        name=dataset_name,
        description=str(data),
        customProperties=data
    )

    mcp = MetadataChangeProposalWrapper(
        entityUrn=dataset_urn,
        aspect=dataset_properties
    )

    # Write the metadata change proposal to DataHub
    emitter.emit(mcp)

def emit_lineage_mce(emitter, group, upstream_digis, downstream_digi):
    upstream_urns = [builder.make_dataset_urn(group, upstream_digi) for upstream_digi in upstream_digis]
    downstream_urn = builder.make_dataset_urn(group, downstream_digi)
    lineage_mce = builder.make_lineage_mce(upstream_urns, downstream_urn)
    emitter.emit_mce(lineage_mce)

# emit digi metadata forever
def emit_digi_data_forever(datahub_endpoint, datahub_group):
    emitter = get_emitter(datahub_endpoint)
    
    while True:
        # Create an instance of the API class
        api_instance = client.CustomObjectsApi()

        version = "v1"
        all_digis = []
        try:
            # get all digis within dspace
            groups = client.ApisApi().get_api_versions().groups
            for group_config in groups:
                group = group_config.name

                # only get CRDs corresponding to digis
                if "digi.dev" not in group:
                    continue

                api_response = api_instance.get_api_resources(group, version)
                digis = []
                for resource in api_response.resources:
                    resource_digis = api_instance.list_cluster_custom_object(group, version, resource.name)
                    digis.extend(resource_digis["items"])
                
                # emit name, kind, and egresses for each digi
                for d in digis:
                    # emit name, kind, and egresses for each digi
                    digi_name = d["metadata"]["name"]
                    data = {
                        "name": digi_name,
                        "kind": d["kind"]
                    }
                    all_digis.append(f"{group}/{digi_name}")
                    if "egress" in d["spec"]:
                        egresses = d["spec"]["egress"]
                        for e in egresses:
                            egress_name = f"egress:{e}"
                            desc = egresses[e].get("desc")
                            if not desc:
                                desc = ""
                            data[egress_name] = desc
                    emit_new_digi_mcp(emitter, datahub_group, digi_name, data)

                    # emit mounts
                    # TODO: support mounts from different dspaces
                    all_mounted_digis = []
                    if "mount" in d["spec"]:
                        mount_kinds = d["spec"]["mount"]
                        for kind, mounted_digis in mount_kinds.items():
                            for m in mounted_digis:
                                name_pattern = "(.*)/(.*)"
                                name_matches = re.search(name_pattern, m)
                                m_namespace = name_matches.group(1)
                                m_name = name_matches.group(2)
                                all_mounted_digis.append(m_name)
                    if len(all_mounted_digis) != 0:
                        emit_lineage_mce(emitter, datahub_group, all_mounted_digis, digi_name)

            digi.logger.info(f"Writing digis: {all_digis}")
        except Exception as e:
            digi.logger.info("Failed to write dspace data to Datahub: ")
            digi.logger.info(e)

        time.sleep(10)
