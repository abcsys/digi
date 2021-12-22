import digi
import digi.util as util

DEFAULT_INTERVAL = 0.2


@digi.on.control
def do_control(sv):
    pause = util.get(sv, "pause.intent", True)
    interval = util.get(sv, "interval.intent", DEFAULT_INTERVAL)
    if pause:
        digi.logger.info("pause")
        loader.stop()
    else:
        loader.reset(load_interval=interval)
        loader.start()
    util.update(sv, "pause.status", pause)
    util.update(sv, "interval.status", interval)


def load():
    digi.pool.load(
        [{
            "foo": "bar"
        }]
    )


loader = util.Loader(load_fn=load)

if __name__ == '__main__':
    digi.run()
