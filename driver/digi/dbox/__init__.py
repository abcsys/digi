import digi


# handler filter: if managed skip the handler during reconciliation
def managed(proc_spec, diff, *args, **kwargs):
    _, _ = args, kwargs
    managed = digi.util.get(proc_spec, "meta.managed", False)
    if managed:
        return False
    else:
        return digi.filter.path_changed(diff, ("meta", "managed")) or \
               digi.filter.changed(proc_spec, diff, *args, **kwargs)
