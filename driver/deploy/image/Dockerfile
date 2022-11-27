FROM python:3.8
WORKDIR /src/

# TBD multi-stage build with slim base image
RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf && git checkout digi && pip install -e .

COPY driver ./driver
RUN pip install -e ./driver

COPY *.txt *.yml *.yaml ./
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

COPY *.py ./
CMD python3 handler.py
