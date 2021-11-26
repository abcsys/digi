ifndef DIGIHOME
override DIGIHOME = ~/.digi
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
.PHONY: init gen patch model all delete image list edit
init:
	cd $(WORKDIR) && mkdir $(KIND) >/dev/null 2>&1 || true && \
	echo "$$model" > $(KIND)/model.yaml
gen:
	cd $(WORKDIR); REPO=$(REPO) python $(DIGIHOME)/gen.py $(KIND)
patch:
	cd $(WORKDIR); python $(DIGIHOME)/patch.py $(KIND)
model:
	cd $(WORKDIR)/$(KIND) && kubectl apply -f crd.yaml >/dev/null
all: | gen patch model
	$(info model)
delete:
	cd $(WORKDIR)/$(KIND) >/dev/null 2>&1; kubectl delete -f crd.yaml 2>/dev/null || true
	rm -r $(WORKDIR)/$(KIND) >/dev/null 2>&1 || true
image:
	cd $(WORKDIR) && ls -d */* 2> /dev/null | grep "model.yaml" | xargs -I {} dirname {}
list:
	kubectl get deploy --no-headers -o custom-columns=":metadata.name"
edit:
	kubectl edit $(KIND) $(NAME)

.PHONY: test
# test configs
g := $(TAG).digi.dev
v := v1
r := $(KIND)s
n := $(KIND)-test
ns := default

test: | model all
	cd $(WORKDIR)/$(KIND)/test; kubectl delete $(KIND) $(n); kubectl apply -f cr.yaml
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
	cd $(build_dir); sudo docker build -t $(REPO)/$(KIND):$(TAG) -f deploy/image/Dockerfile . || true
	sudo docker push $(REPO)/$(KIND):$(TAG)|| true
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
run: | prepare model
	# stop any existing: delete model, driver, pool
	kubectl delete $(KIND) $(NAME) >/dev/null 2>&1 || true
	helm uninstall $(NAME) >/dev/null 2>&1 || true
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- zapi drop -f $(NAME) >/dev/null 2>&1 || true
	# deploy anew: create model, driver, pool
	# TBD make pool optional by checking values.yaml
	cd $(build_dir)/deploy; mv cr.yaml ./templates; \
	helm install -f values.yaml --set name=$(NAME) $(NAME) . >/dev/null && \
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname`\
    -- zapi create $(NAME) >/dev/null
	rm -r $(build_dir) || true
stop:
	kubectl delete $(KIND) $(NAME) >/dev/null && \
	helm uninstall $(NAME) >/dev/null && \
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- zapi drop -f $(NAME) >/dev/null
print:
	kubectl get samples sample -oyaml | kubectl neat

# lake
ifndef LAKE
override LAKE = lake
endif
.PHONY: query port
# TBD enforce single lake or use service to identify lake
query:
	kubectl exec -it `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
        -- zapi query "$(QUERY)"
port:
	kubectl port-forward service/$(LAKE) 9867:6534 || tru

# debug
.PHONY: log
log:
	kubectl logs `kubectl get pod --field-selector status.phase=Running \
	-l name=$(NAME) -oname --sort-by=.status.startTime | tail -n1 | sed "s/^.\{4\}//"`
