import datetime
import digi
from digi.util import Loader

if __name__ == '__main__':
    digi.run()
    Loader(lambda: digi.pool.load([{
        "load_ts": datetime.datetime.now(),
    }])).start()
