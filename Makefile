# replace with your own container repo
DRIVER_REPO = silveryfu

# default to rootless docker; may set to
# `sudo docker` depending on your setup
DOCKER_CMD = docker

# default location for scripts and configs
HOMEDIR=~/.digi

SOURCE=$(GOPATH)/src/digi.dev/digi

.PHONY: dep digi install
dep:
	# k8s tooling
	# install kubectl: https://kubernetes.io/docs/tasks/tools/#kubectl
	# install krew: https://krew.sigs.k8s.io/docs/user-guide/setup/install/
	# kubectl-neat
	cd /tmp; go get github.com/silveryfu/kubectl-neat@digi && \
	mkdir ~/.krew >/dev/null 2>&1 || true && \
	cp $(GOPATH)/bin/kubectl-neat ~/.krew/bin/kubectl-neat
	# local zed cli (optional)
	cd /tmp; git clone https://github.com/silveryfu/zed.git && \
	cd zed; make install; cd ..; rm -rf zed
	# local zed python lib (optional)
	pip3 install "git+https://github.com/silveryfu/zed#subdirectory=python/zed"
digi:
	cd cmd/; go install ./digi ./dq ./ds ./di
install: | digi
	mkdir $(HOMEDIR) >/dev/null 2>&1 || true
	rm $(HOMEDIR)/lake $(HOMEDIR)/sync $(HOMEDIR)/mount >/dev/null 2>&1 || true
	ln -s $(SOURCE)/lake/ $(HOMEDIR)/lake
	ln -s $(SOURCE)/space/sync/ $(HOMEDIR)/sync
	ln -s $(SOURCE)/space/mount/ $(HOMEDIR)/mount
	sed 's/DRIVER_REPO_TEMP/$(DRIVER_REPO)/g; s/DOCKER_CMD_TEMP/$(DOCKER_CMD)/g' \
	./model/Makefile > $(HOMEDIR)/Makefile && \
	cp ./model/gen.py $(HOMEDIR) && cp ./model/patch.py $(HOMEDIR)

.PHONY: fmt tidy
fmt:
	gofmt -s -w .
	git diff --exit-code -- '*.go'
tidy:
	go mod tidy
	git diff --exit-code -- go.mod go.sum

.PHONY: k8s
k8s:
	minikube start
	# use minikube registry: eval $(minikube docker-env)

.PHONY: playground pg
playground:
	$(info TBD)
pg: | playground
	$(info start playground)
