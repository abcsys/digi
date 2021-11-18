ifndef DIGIHOME
override DIGIHOME = ~/.dq
endif

ifndef WORKDIR
override WORKDIR = .
endif

ifndef REPO
override REPO = silveryfu
endif

ifndef DIGIREPO
override DIGIREPO = /tmp/digirepo
endif

ifndef TAG
override TAG = latest
endif

kc := kubectl
digi_src := $(GOPATH)/src/digi.dev/digi
driver_dir := $(digi_src)/driver
driver_handler := $(WORKDIR)/$(KIND)/driver/*
digi_config := $(WORKDIR)/$(KIND)/deploy/*
build_dir := /tmp/digi-build-$(KIND)-$(TAG)

define model
group: digi.dev
version: v1
kind: $(KIND)
endef
export model

# model
.PHONY: init gen patch model all delete list
init:
	cd $(WORKDIR) && mkdir $(KIND) >/dev/null 2>&1 || true && \
	echo "$$model" > $(KIND)/model.yaml
gen:
	cd $(WORKDIR); python $(DIGIHOME)/gen.py $(KIND)
patch:
	cd $(WORKDIR); python $(DIGIHOME)/patch.py $(KIND)
model:
	cd $(WORKDIR)/$(KIND) && $(kc) apply -f crd.yaml >/dev/null
all: | gen patch model
	$(info model)
delete:
	cd $(WORKDIR)/$(KIND) >/dev/null 2>&1; $(kc) delete -f crd.yaml 2>/dev/null || true
	rm -r $(WORKDIR)/$(KIND) >/dev/null 2>&1 || true
list:
	cd $(WORKDIR); ls -d */* 2> /dev/null | grep "model.yaml" | xargs dirname

.PHONY: test

# test configs
g := $(TAG).digi.dev
v := v1
r := $(KIND)s
n := $(KIND)-test
ns := default

test: | model all
	cd $(WORKDIR)/$(KIND)/test; $(kc) delete $(KIND) $(n); $(kc) apply -f cr.yaml
	GROUP=$(g) VERSION=$(v) PLURAL=$(r) NAME=$(n) NAMESPACE=$(ns) MOUNTER=$(MOUNTER) \
	python $(WORKDIR)/$(KIND)/driver/handler.py

# driver
.PHONY: prepare
prepare:
	rm -r $(build_dir) >/dev/null 2>&1 || true
	mkdir -p $(build_dir)/deploy/
	rsync -r $(driver_dir) $(build_dir) || true
	rsync -r $(driver_dir)/deploy $(build_dir) || true
	# app specific configs overwrite the generic ones
	rsync -r $(digi_config) $(build_dir)/deploy || true
	rsync -r $(driver_dir)/requirements.txt $(build_dir) || true

.PHONY: build
build: | prepare gen patch
	rsync $(driver_handler) $(build_dir)/ || true
	# use DOCKER_BUILDKIT=0 to enable more messages
	cd $(build_dir); docker build -t $(REPO)/$(KIND):$(TAG) -f deploy/image/Dockerfile . || true
	docker push $(REPO)/$(KIND):$(TAG)|| true
	rm -r $(build_dir) || true

# image
.PHONY: push pull
push:
	mkdir $(DIGIREPO) >/dev/null 2>&1 || true
	cd $(WORKDIR); tar czf $(KIND).gz $(KIND) && mv $(KIND).gz $(DIGIREPO)/ >/dev/null || true
pull:
	cd $(WORKDIR); rsync $(DIGIREPO)/$(KIND).gz . && tar xzf $(KIND).gz && rm $(KIND).gz > /dev/null

# deploy
.PHONY: run stop print
run: | stop prepare model
	cd $(build_dir)/deploy; mv cr.yaml ./templates; \
	helm install -f values.yaml --set name=$(NAME) $(NAME) . >/dev/null || true \
	rm -r $(build_dir) || true
stop:
	$(kc) delete $(KIND) $(NAME) >/dev/null 2>&1 || true
	helm uninstall $(NAME) >/dev/null 2>&1 || true
print:
	$(kc) get samples sample -oyaml | $(kc) neat

# debug
.PHONY: log
log:
	kubectl logs `kubectl get pod --field-selector status.phase=Running \
	-l name=$(NAME) -oname --sort-by=.status.startTime | tail -n1 | sed "s/^.\{4\}//"`
