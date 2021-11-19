import sys
import subprocess

import digi

@digi.on.model
def h(pools, old):
    digi.logger.info("old", old)
    digi.logger.info(pools)


if __name__ == '__main__':
    try:
        subprocess.check_call("ZED_LAKE_ROOT=/mnt/lake zed lake serve >/dev/null 2>&1 &",
                              shell=True)
    except subprocess.CalledProcessError:
        digi.logger.fatal("unable to start zed lake")
        sys.exit(1)

    digi.logger.info("started zed lake")
    digi.run()
