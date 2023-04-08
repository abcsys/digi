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


# Each digi can be a data source that has egress attributes.
# Each egress attribute maps to a data pool branch, e.g., l1@main.
# A source is uniquely identified by its group, version, kind,
# name, namespace, and the egress ID/name. The source attribute
# is parsed with the following rules:
# - If all attributes are given, a single egress branch is identified.
# - If the egress ID is omitted, default to main branch at the source pool.
# - If the name is omitted, default to all sources with of same kind mounted
#   to the destination.
# - If the group / version / kind is omitted, default to the destination's
#   corresponding attribute.
#   - XXX self-reference is allowed with ingress pointing to the
#     destination itself
# TBD add tests
def resolve_by_mount(source: typing.Union[dict, str], *,
                     exist_only: bool = True) -> typing.List[str]:
    """
    Return the list of egress pool@branch given source attributes.
    """
    if isinstance(source, dict):
        branch = source.get("egress", "main")
        # XXX assume name is a unique id to digi and ignore namespace
        if "name" in source:
            return [f"{source['name']}@{branch}"]
        else:
            group = source.get("group", digi.group)
            version = source.get("version", digi.version)
            kind = source.get("kind", digi.kind)

    elif isinstance(source, str):
        parts = source.split("@")
        branch = parts[1] if len(parts) > 1 else "main"
        if "kind:" not in parts[0]:
            return [f"{parts[0]}@{branch}"]
        else:
            # kind:g/v/k@main or kind:k@main; k <-> r
            kind = parts[0].lstrip("kind:")
            group, version, kind = digi.util.parse_kind(kind)
    else:
        raise NotImplementedError

    if kind == "any":
        mounts = digi.model.get_mount(any=True)
    else:
        mounts = digi.model.get_mount(group, version, inflection.pluralize(kind))
    pools = [digi.util.trim_default_namespace(name) for name in mounts.keys()] \
        if mounts else []

    return [f"{pool}@{branch}"
            for pool in pools if not exist_only
            or digi.data.lake.branch_exist(pool, branch)]
