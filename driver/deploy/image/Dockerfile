FROM python:3.7
WORKDIR /src/

RUN git clone https://github.com/silveryfu/zed.git && \
    mv zed/python/zed zed-cli && pip install -e zed-cli && rm -r zed/
RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf; git checkout digi && pip install -e .

COPY driver ./driver
RUN cd driver; pip install -e .

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

COPY *.py .
CMD python3 handler.py
