.PHONY: tinyload
tinyload:
	digi run tinyload t1
	watch -n1 time "digi query t1 'count()'"

.PHONY: tinysync
tinysync:
	digi run tinysync t1
	sleep 2
	digi query t1@out "latency:=cast((ts - load_ts), <string>) | cut latency | head 10"

.PHONY: stop
stop:
	digi stop `digi ls -q`
