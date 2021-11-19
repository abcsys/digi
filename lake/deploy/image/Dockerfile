FROM golang:1.16 as zed
WORKDIR /src/

RUN git clone https://github.com/silveryfu/zed.git && \
    cd zed; make install

FROM python:3.7
COPY --from=zed /go/bin /usr/bin

RUN git clone https://github.com/silveryfu/zed.git && \
    pip install -e zed/python/zed
RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf; git checkout low-lat; pip install -e .

COPY . .
RUN (ls thirdparty.txt >> /dev/null 2>&1 && pip install -r thirdparty.txt) || true
RUN cd driver; pip install -e .

CMD python3 handler.py
