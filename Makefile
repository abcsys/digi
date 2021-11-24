NAME=digi
HOMEDIR=~/.digi

.PHONY: digi install dep
digi:
	cd cmd/; go install ./digi ./dq ./ds
dep:
	go get github.com/brimdata/zed
install: | digi
	mkdir $(HOMEDIR) >/dev/null 2>&1 || true
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
