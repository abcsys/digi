import sys
import subprocess

import digi
from digi import util


def get_target_name():
    return digi.name.rstrip("-view")


def export():
    subprocess.check_call(f"zed query -lake "
                          f"http://lake:6534 -f csv -o 'from {get_target_name()} | not _type'",
                          shell=True)


exporter = util.Loader(export)
exporter.start()

if __name__ == '__main__':
    try:
        subprocess.check_call("materialized -w 1 >/dev/null 2>&1 &",
                              shell=True)
    except subprocess.CalledProcessError:
        print("unable to start materialized")
        sys.exit(1)

    print("started materialized")
    digi.run()
    print(f"digi name {get_target_name()}")
