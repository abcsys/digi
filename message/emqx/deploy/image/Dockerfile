# EMQX
FROM emqx/emqx:5.0.18 as emqx

# Digi
FROM python:3.8

COPY --from=emqx /usr/local/bin/emqx /bin/emqx

WORKDIR /src/

RUN git clone https://github.com/silveryfu/kopf.git && \
    cd kopf && git checkout digi && pip install -e .

COPY driver ./driver
RUN pip install -e ./driver

COPY *.txt .
RUN pip install -r thirdparty.txt > /dev/null 2>&1 || true

COPY *.py .
CMD python3 handler.py
