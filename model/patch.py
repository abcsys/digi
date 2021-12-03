import yaml
import os
import sys
import pprint as pp
from collections import defaultdict

"""
Go through all CRDs in current directory and patch each with the corresponding mounts.

Work with OpenAPIV3 only.
"""

_dir_path = os.path.join(os.path.curdir)


def gvr(g, v, r):
    return g + "/" + v + "/" + r


def patch_mount(_gvr, crd, parent_gvr, parent_crd):
    # get child's spec
    _v = _gvr.split("/")[1]
    spec, result = None, None
    for v in crd["spec"]["versions"]:
        if v["name"] == _v:
            spec = v["schema"]["openAPIV3Schema"]["properties"]["spec"]
    assert spec

    # patch the parent
    _parent_v = parent_gvr.split("/")[1]
    for v in parent_crd["spec"]["versions"]:
        if v["name"] == _parent_v:
            parent_spec = v["schema"]["openAPIV3Schema"]["properties"]["spec"]["properties"]
            assert "mount" in parent_spec
            mount = parent_spec["mount"]["properties"]
            assert _gvr in mount
            mount[_gvr]["additionalProperties"]["properties"]["spec"] = spec


def patch():
    # XXX multiple versions might fail
    model_dirs = filter(os.path.isdir, os.listdir(_dir_path))

    # crd yamls
    f_crds = dict()

    # crd json keyed by pluralized model id (gvr), e.g., mock.digi.dev/v1/lamps
    crds = dict()

    # crd dependencies, tracked by the mounting model
    crd_deps = defaultdict(set)

    # tracks which crds belong in the same file; each group is id by the first crd's gvr
    crd_groups = defaultdict(list)

    # load crds
    for md in model_dirs:
        if md.startswith("."):
            continue
        f_crd = os.path.join(_dir_path, md, "crd.yaml")
        if not os.path.isfile(f_crd):
            continue
        with open(f_crd) as f:
            _crds = list(yaml.load_all(f, Loader=yaml.FullLoader))
            if _crds is None:
                continue
        crd_group = None
        for crd in _crds:
            group = crd["spec"]["group"]
            plural = crd["spec"]["names"]["plural"]
            for v in crd["spec"]["versions"]:
                _gvr = gvr(group, v["name"], plural)
                crds[_gvr] = crd
                f_crds[_gvr] = f_crd

                # find deps
                spec = v["schema"]["openAPIV3Schema"]["properties"]["spec"]["properties"]
                if "mount" not in spec:
                    continue

                for m_gvr, _ in spec["mount"]["properties"].items():
                    crd_deps[_gvr].add(m_gvr)
            if crd_group is None:
                crd_group = list()
                crd_groups[_gvr] = crd_group
            crd_group.append(crd)

    # fix the mounts, starting from the dependency-free crds
    while len(crds) > 0:
        _gvr = None
        for _gvr, crd in crds.items():
            if _gvr in crd_deps and len(crd_deps[_gvr]) != 0:
                continue
            break
        assert _gvr

        for parent_gvr, parent_deps in crd_deps.items():
            if _gvr in parent_deps:
                patch_mount(_gvr, crds[_gvr], parent_gvr, crds[parent_gvr])
                parent_deps.remove(_gvr)
        _ = crds.pop(_gvr)

    for _gvr, _crds in crd_groups.items():
        with open(f_crds[_gvr], "w") as f:
            yaml.dump_all(_crds, f)
            # ..,sort_keys=False


if __name__ == '__main__':
    patch()
