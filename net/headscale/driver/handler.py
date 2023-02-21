import sys
import subprocess

import digi


if __name__ == '__main__':
    try:
        subprocess.check_call("headscale serve &", shell=True)
        pass
    except subprocess.CalledProcessError:
        digi.logger.fatal("unable to start net")
        sys.exit(1)

    digi.logger.info("started net")
    digi.run()
