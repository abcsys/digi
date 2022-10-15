import sys
import subprocess

import digi


if __name__ == '__main__':
    try:
        subprocess.check_call("emqx start &", shell=True)
    except subprocess.CalledProcessError:
        digi.logger.fatal("unable to start emqx")
        sys.exit(1)

    digi.logger.info("started emqx")
    digi.run()
