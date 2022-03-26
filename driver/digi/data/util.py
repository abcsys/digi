import typing
import inflection
import zed
import digi
from digi.data import lake_url


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
def parse_source(source: typing.Union[dict, str]) -> typing.List[str]:
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

    # TBD search by watch
    mounts = digi.model.get_mount(group, version, inflection.pluralize(kind))
    digi.logger.info(f"DEBUG: {group} {version} {kind} {mounts}")
    if mounts:
        return [f"{digi.util.trim_default_space(name)}@{branch}"
                for name in mounts.keys()]
    return []


def create_branches_if_not_exist(pool: str, names: list):
    client = zed.Client(base_url=lake_url)
    records = client.query(f"from {pool}:branches")
    branches = set(r["branch"]["name"] for r in records)
    for name in names:
        if name in branches:
            continue
        create_branch(client, pool, name)


def create_branch(client, pool, name,
                  commit=f"0x{'0' * 40}"):
    """TBD move to zed/zed.py"""
    r = client.session.post(client.base_url + f"/pool/{pool}",
                            json={
                                "name": name,
                                "commit": commit,
                            })
    if r.status_code >= 400:
        try:
            error = r.json()['error']
        except Exception:
            r.raise_for_status()
        else:
            raise zed.RequestError(error, r)
