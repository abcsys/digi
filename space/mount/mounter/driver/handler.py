import os
import logging
from digi import mount


def run():
    # TBD read from the mount model
    # TBD dq ->
    mount.Mounter(os.environ["GROUP"],
                  os.environ["VERSION"],
                  os.environ["PLURAL"],
                  os.environ["NAME"],
                  os.environ.get("NAMESPACE", "default"),
                  log_level=int(os.environ.get("LOGLEVEL", logging.INFO))) \
        .start()


if __name__ == '__main__':
    run()
