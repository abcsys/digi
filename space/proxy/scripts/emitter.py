from driver.anysource.datahub import get_emitter, emit_new_digi_mcp

import time

def test_counter_datasets():
    emitter = get_emitter()
    counter = 0
    while True:
        emit_new_digi_mcp(emitter, 42, f"{counter}", data={
            "count": f"{counter}"
        })
        counter += 1
        time.sleep(10)

if __name__ == "__main__":
    test_counter_datasets()
