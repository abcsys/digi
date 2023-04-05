#!/usr/bin/env python3

import os
import sys
import yaml
import inflection

"""
Generate dSpace CRD from templates and configuration file (model.yaml).

TBD: a principled version from k8s code generators.
"""

_header = """
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: {name}
spec:
  group: {group}
  names:
    kind: {kind}
    listKind: {kind}List
    plural: {plural}
    singular: {singular}
  scope: Namespaced
  versions:
"""

_version_spec = """
name: {version}
schema:
  openAPIV3Schema:
    properties:
      apiVersion:
        type: string
      kind:
        type: string
      metadata:
        type: object
      spec:
        properties:
        type: object
    type: object
served: true
storage: true
"""

_meta = """
meta:
  properties:
  type: object
"""

_control = """
control:
  properties:
  type: object
"""
_control_intent = """
intent:
  properties:
  type: object
"""
_control_status = """
status:
  properties:
  type: object
"""
_attr = """
type: {datatype}
"""
_intent_status_attr = """
properties:
  intent:
    type: {datatype}
  status:
    type: {datatype}
type: object
"""
_array_attr = """
items:
  type: {datatype}
type: array
"""


_data = """
data:
  properties:
  type: object
"""
_data_input = """
input:
  properties:
  type: object
"""
_data_output = """
output:
  properties:
  type: object
"""
_data_attr = """
type: {datatype}
"""

_obs = """
obs:
  properties:
  type: object
"""

_mount = """
mount:
  properties:
  type: object
"""
_mount_attr = """
additionalProperties:
  properties:
    mode:
      type: string
    status:
      type: string
    generation:
      type: number
  type: object
type: object
"""

_ingress = """
ingress:
  properties:
  type: object
"""
_ingress_attr = """
properties:
  source:
    items:
      properties:
        group: 
          type: string
        version:
          type: string
        kind: 
          type: string
        name:
          type: string
        namespace:
          type: string
        egress:
          type: string
      type: object
    type: array
  sources:
    items:
      type: string
    type: array
  flow:
    type: string 
  flow_agg:
    type: string
  eoio:
    type: boolean
  patch_source:
    type: boolean
  pause:
    type: boolean
  use_sourcer:
    type: boolean
type: object
"""

_egress = """
egress:
  properties:
  type: object
"""
_egress_attr = """
properties:
  flow:
    type: string 
  eoio:
    type: boolean
  driver_managed:
    type: boolean
  pause:
    type: boolean
type: object
"""

_reflex = """
reflex:
  additionalProperties:
    properties:
      policy:
        type: string
      processor:
        type: string
      priority:
        type: number
    type: object
  type: object
"""
_reflex_attr = """
"""

_misc = """
{name}:
"""
_misc_attr = """
type: {datatype}
"""

_cr = """
apiVersion: {groupVersion}
kind: {kind}
metadata:
  name: {name}
"""

_helm_values = """
name: {name}
namespace: {namespace}
group: {group}
version: {version}
kind: {kind}
plural: {plural}
mounter: {mounter}

image: {repo}/{image}:{tag}
imagepull: {imagepull}
"""

_handler = """import digi


@digi.on.model
def h(model):
    ...


if __name__ == '__main__':
    digi.run()

"""

_visual = """import digi

# This file overwrites visual.py in digi module.

if __name__ == '__main__':
    digi.run()

"""


def pluralize_lower(s: str):
    s = s.lower()
    return {
        "campus": "campuses"
    }.get(s, inflection.pluralize(s))


def make_attr(_name, _attr_tpl, _main_tpl, src_attrs, use_intent_status=False):
    '''
    Fill in attributes of a given template using src_attrs from the model.

    _name: name of the attribute
    _attr_tpl: template for the attribute. If None, use default attribute templates(_attr, _array_attr, _intent_status_attr).
    _main_tpl: main template to fill in(i.e. control, data, etc.)
    src_attrs: attributes from the model
    use_intent_status: flag to use intent and status as the attribute template. May be used to create control attributes.
    '''
    attrs, result = dict(), dict()
    default_tpls = _attr_tpl == None
    # XXX currently this applies to reflex attr only
    if isinstance(src_attrs, str):
        return yaml.load(_main_tpl, Loader=yaml.FullLoader)

    for _n, t in src_attrs.items():
        if not isinstance(t, str):
            assert isinstance(t, dict)
            # TBD simplify the gen rules
            if _n == "openapi":
                attrs = t
            elif "openapi" in t:
                attrs[_n] = t.get("openapi", t)
            else:
                # if a nested attribute, recurse to make the attr
                attrs[_n] = make_attr(_n, None, None, t)[_n]
        else:
            # if not a special attr, use the default attr templates
            if default_tpls:
                if use_intent_status:
                    _attr_tpl = _intent_status_attr
                else:
                    if 'array' in t:
                        _attr_tpl = _array_attr
                        # remove array[] from type
                        t = t.replace('array', '')[1:-1]
                    else:
                        _attr_tpl = _attr
            attrs[_n] = yaml.load(_attr_tpl.format(name=_n, datatype=t),
                                  Loader=yaml.FullLoader)
    if len(attrs) > 0:
        if _main_tpl:
            result = yaml.load(_main_tpl, Loader=yaml.FullLoader)
        else:
            result = dict()
        if _name in result and result[_name] is not None and "properties" in result[_name]:
            result[_name]["properties"] = attrs
        else:
            result[_name] = attrs
    return result


def make_data_attr(model):
    _input = make_attr("input", _data_attr, _data_input,
                       src_attrs=model.get("data", {}).get("input", {}))
    _output = make_attr("output", _data_attr, _data_output, src_attrs=model.get(
        "data", {}).get("output", {}))
    if len(_input) + len(_output) == 0:
        return {}
    result = yaml.load(_data, Loader=yaml.FullLoader)
    result["data"]["properties"] = dict()
    result["data"]["properties"].update(_input)
    result["data"]["properties"].update(_output)
    return result


def gen_crd(model: str) -> str:
    '''
    Generate CRD yaml string from model string.

    model: model string
    '''

    header = _header.format(name=pluralize_lower(model["kind"]) + "." + model["group"],
                            group=model["group"],
                            kind=model["kind"],
                            plural=pluralize_lower(model["kind"]),
                            singular=model["kind"].lower())
    header = yaml.load(header, Loader=yaml.FullLoader)

    # fill in attributes
    meta = make_attr("meta", None, _meta, src_attrs=model.get("meta", {}))
    control = make_attr("control", None, _control, src_attrs=model.get(
        "control", {}), use_intent_status=True)
    data = make_data_attr(model)
    obs = make_attr("obs", None, _obs, src_attrs=model.get("obs", {}))
    mount = make_attr("mount", _mount_attr, _mount,
                      src_attrs=model.get("mount", {}))
    ingress = make_attr("ingress", _ingress_attr, _ingress,
                        src_attrs=model.get("ingress", {}))
    egress = make_attr("egress", _egress_attr, _egress,
                       src_attrs=model.get("egress", {}))
    reflex = make_attr("reflex", _reflex_attr, _reflex,
                       src_attrs=model.get("reflex", {}))

    assert not (len(control) > 0 and len(data) >
                0), "cannot have both control and data attrs!"

    # version
    version = _version_spec.format(version=model["version"])
    version = yaml.load(version, Loader=yaml.FullLoader)
    spec = version["schema"]["openAPIV3Schema"]["properties"]["spec"]
    spec["properties"] = dict()
    spec["properties"].update(meta)
    spec["properties"].update(control)
    spec["properties"].update(data)
    spec["properties"].update(obs)
    spec["properties"].update(mount)
    spec["properties"].update(ingress)
    spec["properties"].update(egress)
    spec["properties"].update(reflex)

    # custom attribute
    for k, v in model.items():
        # TBD clean the attribute generation by making the attribute templates a map
        if k not in {"group", "version", "kind", "ingress", "egress",
                     "meta", "control", "data", "obs", "mount", "reflex"}:
            spec["properties"].update(
                make_attr(k, _misc_attr, _misc.format(name=k), src_attrs=v))

    # main TBD: multiple version or incremental versions
    header["spec"]["versions"] = list()
    header["spec"]["versions"].append(version)

    return header


def gen_cr(_dir_path, parent_dir, model, name_=None):
    name_ = model["kind"].lower() if name_ is None else name_

    if not os.path.exists(os.path.join(_dir_path, parent_dir)):
        os.makedirs(os.path.join(_dir_path, parent_dir))
    cr_file = os.path.join(_dir_path, parent_dir, "cr.yaml")
    if not os.path.exists(cr_file):
        cr = _cr.format(groupVersion=model["group"] + "/" + model["version"],
                        kind=model["kind"],
                        name=name_,
                        )
        cr = yaml.load(cr, Loader=yaml.FullLoader)
        cr["spec"] = dict()

        # XXX improve CR generation
        for _name in ["meta", "control", "data"]:
            attrs = model.get(_name, {})
            if len(attrs) == 0:
                continue
            if _name not in cr["spec"]:
                cr["spec"][_name] = dict()
            for a, t in attrs.items():
                # XXX nested attributes may lead to unuseful intents
                if _name == "control":
                    v = ""
                    if isinstance(t, str):
                        v = {
                            "string": "",
                            "number": 0,
                        }.get(t, v)
                    cr["spec"][_name].update({a: {
                        "intent": v,
                    }})
                else:
                    v = ""
                    if isinstance(t, str):
                        v = {
                            "string": "",
                            "number": 0,
                        }.get(t, v)
                    cr["spec"][_name].update({a: v})

        with open(cr_file, "w") as f_:
            # TBD add plain-write
            yaml.dump(cr, f_, default_style=None)

        # XXX
        with open(cr_file, "r+") as f_:
            _s = f_.read().replace("'{", "{").replace("}'", "}")
            f_.seek(0)
            f_.truncate()
            f_.write(_s)


def gen(name):
    '''
    Generate templates for a model in a given directory.

    name: directory name
    '''

    _dir_path = os.path.join(os.path.curdir, name)

    with open(os.path.join(_dir_path, "model.yaml")) as f:
        models = list(yaml.load_all(f, Loader=yaml.FullLoader))

    crds = list()
    for model in models:
        # assemble the crd
        crd = gen_crd(model)
        crds.append(crd)

        # generate a CR if missing
        # only the first model's cr will be generated

        # deployment cr
        gen_cr(_dir_path, "deploy", model, name_="'{{ .Values.name }}'")

        # testing cr
        gen_cr(_dir_path, "test", model, name_=model["kind"].lower())

        # generate a helm values.yaml if missing
        values_file = os.path.join(_dir_path, "deploy", "values.yaml")
        if not os.path.exists(values_file):
            values = _helm_values.format(
                group=model["group"],
                version=model["version"],
                kind=model["kind"],
                plural=pluralize_lower(model["kind"]),
                name=model["kind"].lower(),
                namespace=model.get("namespace", "default"),
                mounter="true" if "mount" in model else "false",
                image=f"{model['kind']}.{model['version']}.{model['group']}".lower(),
                repo=os.environ.get("DRIVER_REPO", "local"),
                tag=os.environ.get("DRIVER_TAG", "latest"),
                imagepull=os.environ.get("IMAGEPULL", "Always"),
            )
            values = yaml.load(values, Loader=yaml.FullLoader)

            with open(values_file, "w") as f_:
                yaml.dump(values, f_)

        # generate handlers if missing
        handler_file = os.path.join(_dir_path, "driver", "handler.py")
        if not os.path.exists(os.path.join(_dir_path, "driver")):
            os.makedirs(os.path.join(_dir_path, "driver"))

        if not os.path.exists(handler_file):
            handler = _handler.format()

            with open(handler_file, "w") as f_:
                f_.write(handler)

        # generate visual.py
        if os.environ.get("VISUAL", "false") == "true":
            visual_file = os.path.join(_dir_path, "driver", "visual.py")
            if not os.path.exists(os.path.join(_dir_path, "driver")):
                os.makedirs(os.path.join(_dir_path, "driver"))

            if not os.path.exists(visual_file):
                handler = _visual.format()

                with open(visual_file, "w") as f_:
                    f_.write(handler)

    with open(os.path.join(_dir_path, "crd.yaml"), "w") as f_:
        yaml.dump_all(crds, f_)
        # ..,sort_keys=False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        gen(sys.argv[1])
    else:
        print("gen.py takes a name")
