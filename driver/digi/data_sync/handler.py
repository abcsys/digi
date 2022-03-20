import digi
import digi.data_sync.sync as sync

ingress_sync, egress_sync = dict(), dict()


@digi.on.ingress
def do_ingress(ingress):
    global ingress_sync
    for _, _sync in ingress_sync.items():
        _sync.stop()
    ingress_sync = dict()

    for name, ig in ingress.items():
        sources, dataflow = ig.get("sources", []), ig.get("dataflow", "")
        combine_dataflow = ig.get("combine_dataflow", "")
        _sync = sync.Sync(
            sources=[s + "_egress" for s in sources],
            in_flow=dataflow,
            out_flow=combine_dataflow,
            dest=digi.name,
        )
        ingress_sync[name] = _sync
        _sync.start()
        digi.logger.info(f"started ingress sync {name} "
                         f"with query: {_sync.query_str}")


@digi.on.egress
def do_egress(egress):
    global egress_sync
    for _, _sync in egress_sync.items():
        _sync.stop()
    egress_sync = dict()

    for name, ig in egress.items():
        dataflow = ig.get("dataflow", "")
        _sync = sync.Sync(
            sources=[digi.name],
            in_flow=dataflow,
            out_flow="",
            dest=f"{digi.name}_egress",
        )
        egress_sync[name] = _sync
        _sync.start()
        digi.logger.info(f"started egress sync {name} "
                         f"with query: {_sync.query_str}")
