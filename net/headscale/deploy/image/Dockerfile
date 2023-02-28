# Headscale
FROM headscale/headscale:0.20.0 as headscale

# Digi
FROM python:3.8

COPY --from=headscale /bin/headscale /bin/headscale
COPY deploy/image/config.yaml /etc/headscale/

WORKDIR /src/

RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf && git checkout digi && pip install -e .

COPY driver ./driver
RUN pip install -e ./driver

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

RUN mkdir -p /var/lib/headscale/

COPY *.py .
CMD python3 handler.py
