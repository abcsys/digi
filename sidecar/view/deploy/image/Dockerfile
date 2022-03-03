FROM golang:1.16 as zed
WORKDIR /src/

RUN git clone https://github.com/silveryfu/zed.git && \
    cd zed; make install

FROM python:3.8
COPY --from=zed /go/bin /usr/bin

WORKDIR /src/

# TBD multi-stage build with slim base image
RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf && git checkout digi && pip install -e .
RUN git clone https://github.com/silveryfu/zed.git && \
    mv zed/python/zed zed-cli && pip install -e ./zed-cli && rm -r zed/
COPY driver/requirements.txt ./driver/requirements.txt
RUN cd driver; pip install -r requirements.txt

## Postgres
#RUN apt update && apt install -y lsb-release && \
#    touch /etc/apt/sources.list.d/pgdg.list && \
#    echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
#    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
#    apt update && \
#    apt -y install postgresql

# Materialize
RUN touch /etc/apt/sources.list.d/materialize.list && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 79DEC5E1B7AE7694 && \
    echo "deb http://apt.materialize.com/ generic main" > /etc/apt/sources.list.d/materialize.list && \
    apt update && \
    apt install -y materialized postgresql-client

COPY driver ./driver
RUN pip install -e ./driver

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

COPY *.py .
CMD python3 handler.py
