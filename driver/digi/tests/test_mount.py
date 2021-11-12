import os
import sys
import subprocess
import time
import yaml
import inflection
import digi.util as util

_dir = os.path.dirname(os.path.realpath(__file__))
_mock_dir = os.path.join(_dir, "..", "mocks")
_parent = os.path.join(_mock_dir, "room")
_child = os.path.join(_mock_dir, "lamp")
_parent_cr = os.path.join(_parent, "test", "cr.yaml")
_child_cr = os.path.join(_child, "test", "cr.yaml")
_parent_crd = os.path.join(_parent, "crd.yaml")
_child_crd = os.path.join(_child, "crd.yaml")


def _wait(t=0.5):
    time.sleep(t)


"""
Mount tests:

Create/resume/delete events:
1. create parent model; neat display parent -> parent
2. create child model; neat display child -> child
3. dq mount child parent; neat display parent and child:
    - parent.mount.child
    - parent.mount.child.status matches child.status
    - child.intent matches parent.mount.child.intent
4. dq mount -d child parent; neat display parent and child:
    - parent.mount.child is gone
5. dq mount child parent; kc remove child model; neat display parent
    - parent.mount.child is gone 
6. create child model; neat display parent and child
    - same as 3.

Update events:
1. create parent and child model
2. dq mount child parent
3. update parent.mount.child.intent
    - child.intent matches 
4. update parent.mount.child.status
    - child.status doesn't match
5. update child.status  
    - parent.mount.child.status matches
6. update child.intent
    - parent.mount.child.intent matches
"""


def test_mount(parent, child):
    _make_cr(parent)
    _show(parent, msg="created parent")

    _make_cr(child)
    _show(child, msg="created child")

    _wait()
    _mount(child, parent)

    _wait()
    _show(parent, msg="mounted child to parent")

    _wait(60)
    _mount(child, parent, unmount=True)
    _show(parent, msg="unmounted child")

    _wait(5)
    _mount(child, parent)
    _wait()
    _make_cr(child, delete=True)
    _show(parent, msg="mount child but delete it after")

    _wait()
    _make_cr(child)
    _show(parent, msg="create child again")


def test_prop(parent, child):
    _make_cr(parent)
    _show(parent, msg="created parent")

    _make_cr(child)
    _show(child, msg="created child")

    _wait()
    _mount(child, parent)

    _wait()
    _show(parent, msg="mounted child to parent")

    ps, cs = _get_spec(parent), _get_spec(child)
    for _, ms in ps["spec"]["mount"].items():
        for _, m in ms.items():
            print(m)


# TBD move to pytest
def test_all():
    with _Setup() as s:
        test_mount(s.parent, s.child)

    # with _Setup() as s:
    #     ...
    # test_prop(s.parent, s.child)


def _get_spec(m):
    return util.get_spec(m["g"], m["v"], m["r"],
                         m["n"], m["ns"])


class _Setup:
    @staticmethod
    def _parse(cr):
        with open(cr) as f:
            model = yaml.load(f, Loader=yaml.SafeLoader)
            meta = model["metadata"]
            auri = "/".join(["", model["apiVersion"], model["kind"],
                             meta.get("namespace", "default"),
                             meta["name"]])
            g, v = model["apiVersion"].split("/")
            return {
                "auri": auri,
                "g": g,
                "v": v,
                "k": model["kind"].lower(),
                "n": meta["name"],
                "ns": meta.get("namespace", "default"),
                "r": inflection.pluralize(model["kind"]).lower(),
                "alias": meta["name"],
                "cr_file": cr,
            }

    def __enter__(self):
        _apply(_parent_crd)
        self.parent = self._parse(_parent_cr)
        _apply(_child_crd)
        self.child = self._parse(_child_cr)

        _make_cr(self.parent, delete=True)
        _make_cr(self.child, delete=True)

        _cmd(f"dq alias {self.parent['auri']} {self.parent['alias']}")
        _cmd(f"dq alias {self.child['auri']} {self.child['alias']}")

        _make_driver(self.parent["k"], self.parent["n"], delete=True)
        _make_driver(self.parent["k"], self.parent["n"])

        print("waiting for driver ready...")
        _wait(5)
        return self

    def __exit__(self, *args, **kwargs):
        _make_driver(self.parent["k"], self.parent["n"], delete=True)

        _make_cr(self.parent, delete=True)
        _apply(_parent_crd, delete=True)

        _make_cr(self.child, delete=True)
        _apply(_child_crd, delete=True)


def _mount(child, parent, unmount=False):
    _cmd(f"dq mount {'-d ' if unmount else ''}"
         f"{child['alias']} {parent['alias']}",
         show_cmd=True)


def _make_driver(kind, name, delete=False):
    _cmd(f"cd {_mock_dir}; "
         f"dq {'stop' if delete else 'run'} {kind} {name} | true")


def _make_cr(model, delete=False):
    _apply(model["cr_file"], delete=delete)


def _apply(f, delete=False):
    _cmd(f"kubectl {'delete' if delete else 'apply'} "
         f"-f {f} {'> /dev/null 2>&1 | true' if delete else ''}")


def _show(model, neat=True, msg=""):
    print("\n---" + msg)
    _cmd(f"kubectl get {model['k']} {model['n']} "
         f"-oyaml {'| kubectl neat' if neat else ''}")


def _cmd(cmd, show_cmd=False, quiet=False):
    """Executes a subprocess running a shell command and
    returns the output."""
    if show_cmd:
        print()
        print("$", cmd)

    if quiet:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            executable='/bin/bash')
    else:
        proc = subprocess.Popen(cmd, shell=True,
                                executable='/bin/bash')

    out, _ = proc.communicate()

    if proc.returncode:
        if quiet:
            print('Log:\n', out, file=sys.stderr)
        print('Error has occurred running command: %s' % cmd,
              file=sys.stderr)
        sys.exit(proc.returncode)
    return out


if __name__ == '__main__':
    test_all()
