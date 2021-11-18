import subprocess

import digi
import digi.on as on


if __name__ == '__main__':
    try:
        subprocess.check_call("ZED_LAKE_ROOT=/mnt/lake zed lake serve >/dev/null 2>&1 &",
                              shell=True)
    except subprocess.CalledProcessError:
        print("unable to run zed lake")
        exit(1)

    digi.run()
