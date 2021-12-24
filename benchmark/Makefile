.PHONY: tinyload stop
tinyload:
	digi run tinyload t1
	watch -n1 time "digi query t1 'count()'"
stop:
	digi stop t1
