import digi

ingress_loaders = dict()
egress_loaders = dict()


def make_load(dataflow):
    def load():
        records = digi.pool.query(dataflow)
        # XXX records is a generator, we materialize it anyway
        #   given zed cli doesn't support streaming load
        digi.pool.load(list(records))

    return load


def gen_dataflow(sources, dataflow):
    new_dataflow = ""
    # legs = ""
    # for s in sources:
    #     legs += f"{s} => {dataflow};"
    # return f"from ({legs})"
    # XXX
    return f"from {sources[0]} | {dataflow}"


@digi.on.mount
@digi.on.ingress
def do_ingress(ingress):
    global ingress_loaders
    for _, loader in ingress_loaders.items():
        loader.stop()
    # TBD
    # mount = digi.model.get("mount", {})
    for name, ig in ingress.items():
        dataflow = ig.get("dataflow", "")
        if dataflow != "":
            ingress_loaders[name] = digi.util.Loader(
                load_fn=make_load(dataflow)
            )
            ingress_loaders[name].start()


@digi.on.egress
def do_egress(egress):
    global egress_loaders
    for _, loader in egress_loaders.items():
        loader.stop()

    for name, eg in egress.items():
        dataflow = eg.get("dataflow", "")

        if dataflow != "":
            egress_loaders[name] = digi.util.Loader(
                load_fn=make_load(dataflow)
            )
            egress_loaders[name].start()
