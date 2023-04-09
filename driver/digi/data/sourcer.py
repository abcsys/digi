import typing
import inflection
import requests

import digi

default_sourcer_url = "http://sourcer:7534/resolve"


def resolve(source, use_sourcer=False):
    if use_sourcer:
        return resolve_by_sourcer(source, url=default_sourcer_url)
    else:
        return resolve_by_mount(source)


def resolve_by_sourcer(source, url):
    try:
        # {source_lake_url, sources, success}
        resp = requests.get(url,
                            json={"source_quantifier": source},
                            headers={"Content-Type": "application/json"}).json()

        if resp["success"]:
            digi.logger.info(f"Resolved {source}")
            return resp["sources"]
    except:
        raise Exception(f"Sourcer unable to resolve {source}")


def resolve_by_mount(source: typing.Union[dict, str], *,
                     exist_only: bool = True) -> typing.List[str]:
    """
    Return the list of egress pool@branch given source attributes.
    Each digi can be a data source that has egress attributes.
    Each egress attribute maps to a data pool branch, e.g., l1@main.
    A source is uniquely identified by its group, version, kind,
    name, namespace, and the egress ID/name. The source attribute
    is parsed with the following rules:
    - If all attributes are given, a single egress branch is identified.
    - If the egress ID is omitted, default to main branch at the source pool.
    - If the name is omitted, default to all sources with of same kind mounted
      to the destination.
    - If the group / version / kind is omitted, default to the destination's
    corresponding attribute.
    """
    if isinstance(source, dict):
        egress = source.get("egress", "main")
        if "name" in source:
            return [f"{source['name']}@{egress}"]
        else:
            g = source.get("group", digi.group)
            v = source.get("version", digi.version)
            k = source.get("kind", digi.kind)

    elif isinstance(source, str):
        parts = source.split("@")
        kind_or_name, egress = parts[0], parts[1] if len(parts) > 1 else "main"
        if kind_or_name.startswith("kind:"):  # this is a direct reference
            # format: kind:g/v/k@main or kind:k@main;
            # k <-> r can be used interchangeably
            kind = kind_or_name[5:]  # remove "kind:"
            g, v, k = digi.util.parse_kind(kind)
        else:
            return [f"{kind_or_name}@{egress}"]
    else:
        raise NotImplementedError

    if k == "any":
        mounts = digi.model.get_mount(any=True)
    else:
        mounts = digi.model.get_mount(g, v, inflection.pluralize(k))

    if mounts is None:
        return []
    digi.logger.info(f"sourcer: detect matching mounts {mounts} for {source}")

    pools = [digi.util.trim_default_namespace(name) for name in mounts.keys()]
    digi.logger.info(f"sourcer: resolve {source} to {pools} by mount")

    # TBD support multiple egresses
    # TBD disallow self-reference
    return [f"{pool}@{egress}" for pool in pools
            if not exist_only or digi.data.lake.branch_exist(pool, egress)]
