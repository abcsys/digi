# Digi
FROM python:3.8
WORKDIR /src/

RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf && git checkout digi && pip install -e .

RUN arch=$(arch | sed s/aarch64/arm64/ | sed s/x86_64/amd64/) && \
    wget "https://www.emqx.com/en/downloads/broker/5.0.20/emqx-5.0.20-debian11-${arch}.deb" -O emqx.deb
RUN apt update && apt install -y apt-transport-https \
    ca-certificates curl gnupg-agent software-properties-common
RUN apt install ./emqx.deb

COPY driver ./driver
RUN pip install -e ./driver

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

COPY *.py .
CMD python3 handler.py
