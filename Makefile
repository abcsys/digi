# used in digi build; update below or run
# "digi config --driver-repo" to set the default
# driver container repository (e.g. docker account)
DRIVER_REPO = silveryfu

# default to rootless docker; may set to
# `sudo docker` depending on your setup
DOCKER_CMD = docker

# default location for scripts and configs
HOMEDIR = ~/.digi
HOMEABS:=$(shell cd ~; pwd)
SOURCE = $(GOPATH)/src/digi.dev/digi

VERSION = $(shell git describe --tags --dirty --always)

PREREQUISITES = git docker kubectl helm watch jq rsync
K := $(foreach exec,$(PREREQUISITES),\
        $(if $(shell which $(exec)),,$(error "No $(exec) in PATH")))

.PHONY: dep
dep:
	cd /tmp; git clone https://github.com/silveryfu/zed.git && \
	cd zed; make install; cd ..; rm -rf zed
	pip install -r ./model/requirements.txt

.PHONY: digi neat ctx install
digi:
	cd cmd/; go install ./digi ./dq ./ds ./di ./dbox
neat:
	cd sidecar/neat; go install .
ctx:
	cd sidecar/ctx/cmd/ctx; go install .
install: | digi neat ctx
	@mkdir $(HOMEDIR) >/dev/null 2>&1 || true
	@mkdir $(HOMEDIR)/headscale >/dev/null 2>&1 || true
	@rm $(HOMEDIR)/lake $(HOMEDIR)/space $(HOMEDIR)/message $(HOMEDIR)/net $(HOMEDIR)/sidecar >/dev/null 2>&1 || true
	@touch $(HOMEDIR)/config $(HOMEDIR)/alias
	@ln -s $(SOURCE)/lake/ $(HOMEDIR)/lake
	@ln -s $(SOURCE)/space/ $(HOMEDIR)/space
	@ln -s $(SOURCE)/message/ $(HOMEDIR)/message
	@ln -s $(SOURCE)/sidecar/ $(HOMEDIR)/sidecar
	@sed $(SED_EXPR) ./model/Makefile > $(HOMEDIR)/Makefile
	@cp ./model/gen.py $(HOMEDIR) && cp ./model/patch.py $(HOMEDIR) && cp ./model/helper.py $(HOMEDIR)
	@cp -r ./scripts/ $(HOMEDIR)/scripts/ && chmod -R +x $(HOMEDIR)/scripts/
	@cp -r $(SOURCE)/net/ $(HOMEDIR)/net && cat ./net/headscale/deploy/values.yaml | sed s+{{home}}+$(HOMEABS)+g > $(HOMEDIR)/net/headscale/deploy/values.yaml

.PHONY: python-digi
python-digi:
	pip install -e ./driver

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
		--from-file=.dockerconfigjson=~/.docker/config.json \
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
