from driver.anysource.datahub import get_emitter, emit_metadata_event

import time

def test_counter_datasets():
    emitter = get_emitter()
    counter = 0
    while True:
        emit_metadata_event(emitter, 42, f"{counter}", data={
            "count": f"{counter}"
        })
        counter += 1
        time.sleep(10)

if __name__ == "__main__":
    test_counter_datasets()
