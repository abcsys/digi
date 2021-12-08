ifndef DIGIHOME
override DIGIHOME = ~/.digi
endif

ifndef WORKDIR
override WORKDIR = .
endif

ifndef REPO
override REPO = silveryfu # YOUR_CONTAINER_REPO
endif

ifndef DIGIREPO
override DIGIREPO = /tmp/digirepo
endif

ifndef TAG
override TAG = latest
endif

ifndef DOCKER_CMD
override DOCKER_CMD = docker
# uncomment to run docker with root access
#override DOCKER_CMD = sudo docker
endif

digi_src := $(GOPATH)/src/digi.dev/digi
driver_dir := $(digi_src)/driver
driver_handler := $(WORKDIR)/$(KIND)/driver/*
digi_config := $(WORKDIR)/$(KIND)/deploy/*
build_dir := /tmp/digi-build-$(KIND)-$(TAG)

# model
.PHONY: init gen patch model all delete image list edit
# init configs
ifndef GROUP
override GROUP = digi.dev
endif

ifndef VERSION
override VERSION = v1
endif

define model
group: $(GROUP)
version: $(VERSION)
kind: $(KIND)
endef
export model

init:
	cd $(WORKDIR) && mkdir $(KIND) >/dev/null 2>&1 || true && \
	echo "$$model" > $(KIND)/model.yaml
gen:
	cd $(WORKDIR) && REPO=$(REPO) python $(DIGIHOME)/gen.py $(KIND)
patch:
	cd $(WORKDIR) && python $(DIGIHOME)/patch.py $(KIND)
model:
	cd $(WORKDIR)/$(KIND) && kubectl apply -f crd.yaml >/dev/null
all: | gen patch model
delete:
	cd $(WORKDIR)/$(KIND) >/dev/null 2>&1; kubectl delete -f crd.yaml 2>/dev/null || true
	rm -r $(WORKDIR)/$(KIND) >/dev/null 2>&1 || true
image:
	cd $(WORKDIR) && ls -d */* 2> /dev/null | grep "model.yaml" | xargs -I {} dirname {}
list:
	kubectl get deploy --no-headers -o custom-columns=":metadata.name"
edit:
	kubectl edit $(KIND) $(NAME)

.PHONY: clean-test test
# test configs
ifndef NAME
override NAME = $(KIND)-test
endif

ifndef NAMESPACE
override NAMESPACE = default
endif

clean-test:
	kubectl delete $(KIND) $(NAME) >/dev/null 2>&1 || true
test: | all clean-test
	kubectl apply -f $(WORKDIR)/$(KIND)/test/cr.yaml

	cd $(WORKDIR) && GROUP=`head -n1 $(KIND)/model.yaml | cut -d' ' -f 2` \
	VERSION=`head -n2 $(KIND)/model.yaml | tail -1 | cut -d' ' -f 2` \
    PLURAL=$(PLURAL) NAME=$(KIND)-test NAMESPACE=$(NAMESPACE) \
    POOL_PROVIDER=none MOUNTER=$(MOUNTER) \
	python $(KIND)/driver/handler.py

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
	cd $(build_dir) && $(DOCKER_CMD) build -t $(REPO)/$(KIND):$(TAG) $(BUILDFLAG) -f deploy/image/Dockerfile . || true
	$(DOCKER_CMD) push $(REPO)/$(KIND):$(TAG) $(BUILDFLAG) || true
	rm -r $(build_dir) || true

# image
.PHONY: push pull
push:
	mkdir $(DIGIREPO) >/dev/null 2>&1 || true
	cd $(WORKDIR) && tar czf $(KIND).gz $(KIND) && mv $(KIND).gz $(DIGIREPO)/ >/dev/null || true
pull:
	cd $(WORKDIR) && rsync $(DIGIREPO)/$(KIND).gz . && tar xzf $(KIND).gz && rm $(KIND).gz > /dev/null

# deploy
.PHONY: run stop watch
run: | prepare model
	# stop any existing: delete model, driver, pool
	kubectl delete $(KIND) $(NAME) >/dev/null 2>&1 || true
	helm uninstall $(NAME) >/dev/null 2>&1 || true
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- zapi drop -f $(NAME) >/dev/null 2>&1 || true
	# deploy anew: create model, driver, pool
	# TBD make pool optional by checking values.yaml
	cd $(build_dir)/deploy && mv cr.yaml ./templates; \
	helm install -f values.yaml --set name=$(NAME) $(NAME) . >/dev/null && \
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname`\
    -- zapi create $(NAME) >/dev/null
	rm -r $(build_dir) || true
stop:
	kubectl delete $(KIND) $(NAME) >/dev/null && \
	helm uninstall $(NAME) >/dev/null && \
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- zapi drop -f $(NAME) >/dev/null
watch:
	watch -n$(INTERVAL) -t "kubectl get $(KIND) $(NAME) -oyaml | kubectl neat $(NEATLEVEL)"

# lake
ifndef LAKE
override LAKE = lake
endif
.PHONY: query port
# TBD enforce single lake or use service to identify lake
query:
	kubectl exec -it `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
        -- zapi query $(FLAG) "$(QUERY)"
port:
	kubectl port-forward service/$(LAKE) 9867:6534 || tru

# debug
.PHONY: log
log:
	kubectl logs `kubectl get pod --field-selector status.phase=Running \
	-l name=$(NAME) -oname --sort-by=.status.startTime | tail -n1 | sed "s/^.\{4\}//"`
