FROM python:3.8
WORKDIR /src/

RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf && git checkout digi && pip install -e .

# Red Panda (rpk command line tool)
RUN curl -LO https://github.com/redpanda-data/redpanda/releases/latest/download/rpk-linux-amd64.zip
RUN mkdir -p /src/.local/bin
ENV PATH="${PATH}:/src/.local/bin"
RUN unzip rpk-linux-amd64.zip -d /src/.local/bin/

RUN curl -1sLOf 'https://dl.redpanda.com/nzc4ZYQK3WRGd9sy/redpanda/cfg/setup/bash.deb.sh'
RUN chmod +x ./bash.deb.sh
RUN ./bash.deb.sh && apt install redpanda -y

COPY driver ./driver
RUN pip install -e ./driver

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

# TBD multi-stage build with slim base image
COPY *.py .
CMD python3 handler.py