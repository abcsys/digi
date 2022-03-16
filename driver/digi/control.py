import digi


class Model():
    def get(self):
        return digi.rc.view()

    def patch(self, view):
        _, e = digi.util.patch_spec(digi.g, digi.v, digi.r,
                                    digi.n, digi.ns, view)
        if e != None:
            digi.logger.info(f"patch error: {e}")


def create_model():
    return Model()


model = None
