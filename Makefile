# replace with your own container repo
DRIVER_REPO = silveryfu

# default to rootless docker; may set to
# `sudo docker` depending on your setup
DOCKER_CMD = docker

# default location for scripts and configs
HOMEDIR=~/.digi

.PHONY: dep digi install
dep:
	go get github.com/brimdata/zed
	go get github.com/silveryfu/kubectl-neat && \
	cp $(which kubectl-neat) ~/.krew/bin/kubectl-neat
digi:
	cd cmd/; go install ./digi ./dq ./ds
install: | digi
	mkdir $(HOMEDIR) >/dev/null 2>&1 || true
	sed 's/DRIVER_REPO_TEMP/$(DRIVER_REPO)/g; s/DOCKER_CMD_TEMP/$(DOCKER_CMD)/g' \
	./model/Makefile > $(HOMEDIR)/Makefile && \
	cp ./model/gen.py $(HOMEDIR) && \
	cp ./model/patch.py $(HOMEDIR)

.PHONY: k8s
k8s:
	minikube start

# use minikube registry: eval $(minikube docker-env)
