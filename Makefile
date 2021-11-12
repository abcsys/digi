NAME=digi
HOMEDIR=~/.dq

.PHONY: dq install
dq: 
	cd cmd/dq/; go install .
install: | dq
	$(info dq)
	cp ./model/Makefile $(HOMEDIR) && \
	cp ./model/gen.py $(HOMEDIR) && \
	cp ./model/patch.py $(HOMEDIR)

.PHONY: k8s
k8s:
	minikube start
