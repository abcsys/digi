FROM golang:1.16 as zed
WORKDIR /src/

RUN git clone https://github.com/silveryfu/zed.git && \
    cd zed; make install

FROM python:3.8
COPY --from=zed /go/bin /usr/bin

# below: copied from driver.deploy
WORKDIR /src/

RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf && git checkout digi && pip install -e .

COPY driver ./driver
RUN pip install -e ./driver

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

# TBD multi-stage build with slim base image
COPY *.py .
CMD python3 handler.py
