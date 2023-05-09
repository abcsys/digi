from anysource import registry
import digi

from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv("proxy.env")

app = Flask(__name__)

# load config info
host = os.getenv("HOST")
port = os.getenv("PORT")

# register endpoints
from endpoints.proxy import proxy as proxy_blueprint
app.register_blueprint(proxy_blueprint)


@digi.on.meta
def register_proxy(meta):
    # registry proxy with an Anysource Registry
    registry_endpoint = meta.get("registry_endpoint")
    user_name = meta.get("user_name")
    dspace_name = meta.get("dspace_name")

    registry.register_dspace(registry_endpoint, user_name, dspace_name)

if __name__ == '__main__':
    digi.run()
    
    # run proxy endpoint
    app.run(host=host, port=port)


