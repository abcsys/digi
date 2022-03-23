import digi
import typing
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
def parse_source(source: dict) -> typing.List[str]:
    """
    Given source attributes return its egress's pool@branch.
    """
    branch = source.get("egress", "main")
    # XXX assume name is a unique id to digi and ignore namespace
    if "name" in source:
        return [f"{source['name']}@{branch}"]

    group = source.get("group", digi.group)
    version = source.get("version", digi.version)
    kind = source.get("kind", digi.kind)

    mounts = digi.model.get_mount(group, version, kind)
    if mounts is None:
        return []
    else:
        return [f"{digi.util.trim_default_space(name)}@{branch}"
                for name in mounts.keys()]
