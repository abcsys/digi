"""Views used for model manipulation."""
import os
import copy
from box import Box
from abc import ABC, abstractmethod
from kopf._cogs.structs.diffs import diff

import digi.util as util
from digi.util import deep_set

# XXX fix model and type view
class View(ABC):
    @abstractmethod
    def __init__(self,
                 root: dict,
                 root_key: str = "root",
                 gvr_str=None,
                 trim_gv: bool = True,
                 trim_mount: bool = True,
                 trim_name: bool = True,
                 ):
        self._src = root
        self._root = copy.deepcopy(self._src)
        self._root_key = root_key
        self._old, self._new = None, None

        self._trim_gv = trim_gv
        self._trim_mount = trim_mount
        self._trim_name = trim_name

        self._name = os.environ["NAME"]
        self._ns = os.environ.get("NAMESPACE", "default")

        if gvr_str is None:
            self._r = os.environ["PLURAL"]
            self._gv_str = f"{os.environ['GROUP']}" \
                           f"/{os.environ['VERSION']}"
            self._gvr_str = f"{self._gv_str}/{os.environ['PLURAL']}"
        else:
            gvr_str = util.full_gvr(gvr_str)
            self._r = util.parse_gvr(gvr_str)[-1]
            self._gv_str = "/".join(util.parse_gvr(gvr_str)[:-1])
            self._gvr_str = gvr_str

    @abstractmethod
    def __enter__(self):
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, typ, value, traceback):
        raise NotImplementedError

    @abstractmethod
    def transform(self, root: dict, view: dict):
        raise NotImplementedError

    @abstractmethod
    def materialize(self) -> dict:
        raise NotImplementedError

    def m(self) -> dict:
        # shorthand
        return self.materialize()


class NameView(View):
    """
    Return all models in the current world/root view
    keyed by the namespaced name; if the nsn starts
    with default, it will be trimmed off; the original
    view is keyed by "root". Empty model without "spec"
    will be skipped.

    The __enter__ method constructs the model view from
    the root_view and __exit__ applies the changes back
    to the root_view.

    TBD: add mounts recursively but trim off mounts
      record the path and append on the diff path at exit;
      use _transform in __enter__
    """

    def __init__(self, *args, **kwargs):
        self._nsn_gvr = dict()
        super().__init__(*args, **kwargs)

    def __enter__(self):
        _view = {"root": self._root}
        _mount = self._root.get("mount", {})

        for typ, ms in _mount.items():
            for n, m in ms.items():
                if "spec" not in m:
                    continue
                n = util.trim_default_space(n)
                _view.update({n: m["spec"]})
                self._nsn_gvr[n] = typ

        self._old, self._new = _view, copy.deepcopy(_view)
        return self._new

    def __exit__(self, typ, value, traceback):
        _view = {"root": self._root}
        # diff and apply
        _src = self._src
        _diffs = diff(self._old, self._new)
        for op, path, old, new in _diffs:
            nsn = path[0]
            if nsn == "root":
                deep_set(_src, ".".join(path[1:]), new)
            else:
                typ = self._nsn_gvr[nsn]
                nsn = util.normalized_nsn(nsn)
                path = ["mount", typ, nsn, "spec"] + list(path[1:])
                deep_set(_src, path, new)

    def transform(self, root: dict, view: dict):
        _mount = root.get("mount", {})
        if self._trim_mount:
            trim_mount(root, trim_gv=self._trim_gv)
        for typ, models in _mount.items():
            for name, model in models.items():
                name = util.trim_default_space(name)
                if "spec" not in model:
                    continue

                spec: dict = model["spec"]
                self.transform(spec, view)
                view.update({name: spec})

    def materialize(self):
        root = self._root
        view = {self._root_key: root}
        self.transform(root, view)
        return view


class KindView(View):
    """
    Return models group-by their gvr, if the gv is
    the same as the parent's gv, it will be trimmed
    to only the plural.

    TBDs: ditto
    """

    def __init__(self, *args, **kwargs):
        self._typ_full_typ = dict()
        super().__init__(*args, **kwargs)

    def __enter__(self):
        # _view = {self._r: {"root": self._root_view}}
        _view = {"root": self._root}
        _mount = self._root.get("mount", {})

        for typ, ms in _mount.items():
            _typ = typ.replace(self._gv_str + "/", "") if self._trim_gv else typ
            _view[_typ] = {}
            self._typ_full_typ[_typ] = typ

            for n, m in ms.items():
                if "spec" not in m:
                    continue
                n = util.trim_default_space(n)
                _view[_typ].update({n: m["spec"]})

        self._old, self._new = _view, copy.deepcopy(_view)
        return self._new

    def __exit__(self, typ, value, traceback):
        _src = self._src
        _diffs = diff(self._old, self._new)

        for op, path, old, new in _diffs:
            typ = path[0]
            if typ == "root":
                deep_set(_src, ".".join(path[1:]), new)
            else:
                typ = self._typ_full_typ[typ]
                nsn = util.normalized_nsn(path[1])
                path = ["mount", typ, nsn, "spec"] + list(path[2:])
                deep_set(_src, path, new)

    def transform(self, root: dict, view: dict):
        _mount = root.get("mount", {})
        if self._trim_mount:
            trim_mount(root, trim_gv=self._trim_gv)
        for typ, models in _mount.items():
            _typ = typ.replace(self._gv_str + "/", "") if self._trim_gv else typ
            if _typ not in view:
                view[_typ] = list() if self._trim_name else dict()

            for name, model in models.items():
                name = util.trim_default_space(name)
                if "spec" not in model:
                    continue

                spec: dict = model["spec"]
                self.transform(spec, view)

                view[_typ].append(spec if self._trim_name else {name: spec})

    def materialize(self):
        root = self._root
        if self._trim_name:
            view = {self._root_key: [root]}
        else:
            view = {self._root_key: {self._name: root}}
        self.transform(root, view)
        return view


class CleanView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, typ, value, traceback):
        raise NotImplementedError

    def transform(self, root: dict, view: dict):
        _mount = root.get("mount", {})
        view.update(copy.deepcopy(root))
        if len(_mount) > 0:
            if self._trim_mount:
                trim_mount(view, trim_gv=self._trim_gv)
                return
            view["mount"] = dict()

        for typ, models in _mount.items():
            _typ = typ.replace(self._gv_str + "/", "")
            view["mount"][_typ] = dict()

            for name, model in models.items():
                new_name = util.trim_default_space(name)
                if "spec" not in model:
                    continue

                spec: dict = model["spec"]
                view["mount"][_typ][new_name] = dict()
                self.transform(spec, view["mount"][_typ][new_name])

    def materialize(self) -> dict:
        root, view = self._root, dict()
        self.transform(root, view)
        return view


class DotView(View):
    """Dot accessible models."""
    _char_map = {
        "-": "_",
        ".": "_",
        "/": "_",
        " ": "_",
        "\\": "_",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._src_view = self._src
        self._dot_view = None
        self._dot_view_old = None
        # map between unsafe attributes
        # to original ones
        self._attr_map = dict()

    def __enter__(self):
        # box does not record nor expose a conversion
        # map for the safe attributes, so we do so
        # ahead of time and pass a safe dict to box;
        # the self._attr_map keeps track of any conversion.
        self._dot_view_old = self._to_safe_dict(self._src_view)
        self._dot_view = Box(self._dot_view_old)
        return self._dot_view

    def __exit__(self, exc_type, exc_val, exc_tb):
        _src = self._src_view
        self._dot_view = self._dot_view.to_dict()
        _diffs = diff(self._dot_view_old, self._dot_view)
        for op, path, old, new in _diffs:
            path = [self._attr_map.get(p, p) for p in path]
            deep_set(_src, path, new)

    def transform(self, root: dict, view: dict):
        pass

    def materialize(self) -> dict:
        return self.__enter__()

    def _to_safe_dict(self, d: dict) -> dict:
        safe_d = dict()
        for k, v in d.items():
            orig_k = k
            k = self._to_safe_attr(k)
            self._attr_map[k] = orig_k
            if isinstance(v, dict):
                v = self._to_safe_dict(v)
            safe_d[k] = v
        return safe_d

    @staticmethod
    def _to_safe_attr(s: str):
        for k, v in DotView._char_map.items():
            s = s.replace(k, v)
        return s


# aliases
ModelView, TypeView = NameView, KindView


def trim_mount(v: dict, *,
               trim_all=False,
               trim_gv=True):
    # keep only the names of immediate children
    if not trim_all:
        for gvr, models in v.get("mount", {}).items():
            key = util.trim_gv(gvr) if trim_gv else gvr
            v[key] = list()
            for name, _ in models.items():
                name = util.trim_default_space(name)
                v[key].append(name)
    v.pop("mount", "")
