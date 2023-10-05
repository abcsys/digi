FROM python:3.8
WORKDIR /src/

RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf && git checkout digi && pip install -e .

# Redis
RUN curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list && \
    sudo apt-get update && \
    sudo apt-get install redis -y

COPY driver ./driver
RUN pip install -e ./driver

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

# TBD multi-stage build with slim base image
COPY *.py .
CMD python3 handler.py