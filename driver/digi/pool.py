from abc import ABC, abstractmethod
import zed

lake_url = "http://lake:6534/"

class Pool(ABC):
    @abstractmethod
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def create(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def load(self, data):
        raise NotImplementedError

    @abstractmethod
    def query(self, query):
        raise NotImplementedError


class ZedPool(Pool):
    def __init__(self, name):
        super().__init__(name)
        self.client = zed.Client(base_url=lake_url)

    def create(self):
        self.client.create_pool(self.name)

    def load(self, data):
        self.client.load(self.name, data)

    def query(self, query):
        self.client.query(query)


def pool_name(g, v, r, n, ns):
    _, _, _ = g, v, r
    if ns == "default":
        return f"{n}"
    else:
        return f"{ns}-{n}"
