"""Event filters"""


def always(*args, **kwargs):
    _, _ = args, kwargs
    return True


def has_diff(_, diff, path, *args, **kwargs) -> bool:
    _, _ = args, kwargs
    changed_paths = {(".",): True}
    # TBD: add shared diff for all handlers
    # TBD: support incremental diff

    for op, path_, old, new in diff:
        # on create
        if old is None and len(path_) == 0:
            changed_paths.update(_from_model(new))
        else:
            changed_paths.update(_from_path_tuple(path_))

    if path in changed_paths or len(diff) == 0:
        return True
    return False


def _from_model(d: dict):
    result = dict()
    to_visit = [[d.get("spec", {}), []]]
    for n, prefix in to_visit:
        result[tuple(prefix)] = True
        if type(n) is not dict:
            continue
        for _k, _v in n.items():
            to_visit.append([_v, prefix + [_k]])
    return result


def _from_path_tuple(p: tuple):
    # expand a path tuple to dict of paths
    return {
        # skip "spec"
        p[1:_i + 1]: True
        for _i in range(len(p))
    }
