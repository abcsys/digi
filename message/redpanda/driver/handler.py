import subprocess

import digi

@digi.on.meta
def run_rp_broker(meta):
    advertised_broker = meta.get("advertised_broker")
    if not advertised_broker:
        return
    try:
        subprocess.check_call(f"rpk redpanda start --advertise-kafka-addr '{advertised_broker}' &", shell=True)
        digi.logger.info("started redpanda broker")
    except subprocess.CalledProcessError:
        digi.logger.info("unable to start redpanda broker")

if __name__ == '__main__':
    digi.run()
