NAME=digi
HOMEDIR=~/.digi

.PHONY: digi install
digi:
	cd cmd/digi/; go install .
install: | digi
	$(info dq)
	cp ./model/Makefile $(HOMEDIR) && \
	cp ./model/gen.py $(HOMEDIR) && \
	cp ./model/patch.py $(HOMEDIR)
# Use the following command to invoke build directly without dq:
# WORKDIR=. KIND=lake make -f ~/.dq/Makefile build
# Use minikube registry: eval $(minikube docker-env)

.PHONY: k8s
k8s:
	minikube start

# Lake
ifndef LAKE
override LAKE = lake
endif
.PHONY: port
port:
	kubectl port-forward service/$(LAKE) 9867:6534 || true
