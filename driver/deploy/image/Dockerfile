FROM python:3.7
WORKDIR /src/

RUN git clone https://github.com/silveryfu/zed.git && \
    pip install -e zed/python/zed
RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf; git checkout 1.35.3 && pip install -e .

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

COPY . .
RUN cd driver; pip install -e .

CMD python3 handler.py
