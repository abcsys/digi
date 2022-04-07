# update with your container repo
DRIVER_REPO = rithvikchuppala

# default to rootless docker; may set to
# `sudo docker` depending on your setup
DOCKER_CMD = docker

# default location for scripts and configs
HOMEDIR = ~/.digi
SOURCE = $(GOPATH)/src/digi.dev/digi

VERSION = $(shell git describe --tags --dirty --always)

.PHONY: dep digi install
dep:
	# prerequisites:
	kubectl >/dev/null || "kubectl missing: check https://kubernetes.io/docs/tasks/tools/#kubectl"; exit 1
	kubectl krew >/dev/null || "krew missing: check https://krew.sigs.k8s.io/docs/user-guide/setup/install/"; exit 1
	# kubectl-neat
	cd /tmp; go get github.com/silveryfu/kubectl-neat@digi && \
	mkdir ~/.krew >/dev/null 2>&1 || true && \
	cp $(GOPATH)/bin/kubectl-neat ~/.krew/bin/kubectl-neat
	# kubectx
	kubectl krew install ctx
	# optional: local zed cli
	cd /tmp; git clone https://github.com/silveryfu/zed.git && \
	cd zed; make install; cd ..; rm -rf zed
	# optional: local zed python lib
	pip3 install "git+https://github.com/silveryfu/zed#subdirectory=python/zed"
digi:
	cd cmd/; go install ./digi ./dq ./ds ./di
install: | digi
	mkdir $(HOMEDIR) >/dev/null 2>&1 || true
	rm $(HOMEDIR)/lake $(HOMEDIR)/sync $(HOMEDIR)/mount $(HOMEDIR)/view >/dev/null 2>&1 || true
	ln -s $(SOURCE)/lake/ $(HOMEDIR)/lake
	ln -s $(SOURCE)/space/sync/ $(HOMEDIR)/sync
	ln -s $(SOURCE)/space/mount/ $(HOMEDIR)/mount
	ln -s $(SOURCE)/sidecar/view $(HOMEDIR)/view
	sed $(SED_EXPR) ./model/Makefile > $(HOMEDIR)/Makefile
	cp ./model/gen.py $(HOMEDIR) && cp ./model/patch.py $(HOMEDIR)
python:
	cd driver; pip install -e .

ifndef ARCH
override ARCH = $(shell uname -m)
endif
SED_EXPR = 's/REPO_TEMP/$(DRIVER_REPO)/g; s/CMD_TEMP/$(DOCKER_CMD)/g; s/ARCH_TEMP/$(ARCH)/g'

.PHONY: fmt tidy
fmt:
	gofmt -s -w .
	git diff --exit-code -- '*.go'
tidy:
	go mod tidy
	git diff --exit-code -- go.mod go.sum

.PHONY: k8s docker-login
k8s:
	minikube start
	# use minikube registry: eval $(minikube docker-env)
docker-login:
	docker login
	kubectl delete secret generic regcred >/dev/null 2>&1 || true
	kubectl create secret generic regcred \
		--from-file=.dockerconfigjson=/Users/silv/.docker/config.json \
		--type=kubernetes.io/dockerconfigjson

create-release-assets:
	# cp LICENSE.txt acknowledgments.txt dist/$${zeddir} ;
	# windows
	for os in darwin linux; do \
		digidir=digi-$(VERSION).$${os}-$(ARCH); \
		rm -rf dist/$${digidir} ; \
		mkdir -p dist/$${digidir} ; \
		GOOS=$${os} GOARCH=$(ARCH) go build -o dist/$${digidir} ./cmd/digi ; \
	done
	rm -rf dist/release && mkdir -p dist/release
	cd dist && for d in digi-$(VERSION)* ; do \
		zip -r release/$${d}.zip $${d} ; \
	done
