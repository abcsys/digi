import sys
import digi


class Model():
    def get(self):
        return digi.rc.view()

    def patch(self, view_or_path, value=None, gen=sys.maxsize):
        """If first arg given is a view patch it directly; if not
        use it as the path and use the second to compose the view.
        This is useful when the updated value has a prefix."""
        if isinstance(view_or_path, dict):
            view = view_or_path
        elif isinstance(view_or_path, str):
            path, view = view_or_path, dict()
            fields = path.strip(".").split(".")
            front = view
            for field in fields[:-1]:
                front[field] = dict()
                front = front[field]
            front[fields[-1]] = value
        else:
            raise NotImplementedError

        cur_gen, r, e = digi.util.check_gen_and_patch_spec(
            digi.g, digi.v, digi.r, digi.n, digi.ns,
            view, gen)

        if e != None:
            digi.logger.info(f"patch error: {e}")
        return cur_gen, r, e

    def update(self, *args, **kwargs):
        return self.patch(*args, **kwargs)

    def get_mount(self,
                  group=digi.name,
                  version=digi.version,
                  resource=None,
                  any: bool = False,
                  ) -> dict:
        """If any is set, returns all mounts as name:mount pairs.
        If resource is given, returns all mounts under the resource.
        Otherwise returns the mount root."""
        if any:
            mounts = dict()
            for _, name_mount in digi.rc.view().get("mount", {}).items():
                for name, mount in name_mount.items():
                    mounts[name] = mount
            return mounts
        if resource:
            path = f"mount.'{group}/{version}/{resource}'"
        else:
            path = "mount"
        return digi.util.get(digi.rc.view(), path)


def create_model():
    return Model()
