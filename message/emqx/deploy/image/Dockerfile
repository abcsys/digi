FROM python:3.8
WORKDIR /src/

RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf && git checkout digi && pip install -e . \

# EMQX
RUN curl -s https://assets.emqx.com/scripts/install-emqx-deb.sh | bash
RUN apt-get install emqx

COPY driver ./driver
RUN pip install -e ./driver

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

# TBD multi-stage build with slim base image
COPY *.py .
CMD python3 handler.py
