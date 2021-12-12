ifndef DIGIHOME
override DIGIHOME = ~/.digi
endif

ifndef WORKDIR
override WORKDIR = .
endif

ifndef DIGI_REPO
override DIGI_REPO = /tmp/digirepo
endif

ifndef IMAGE_NAME
override IMAGE_NAME = $(KIND).$(VERSION).$(GROUP)
endif

ifndef DRIVER_REPO
override DRIVER_REPO = DRIVER_REPO_TEMP
endif

ifndef DOCKER_CMD
override DOCKER_CMD = DOCKER_CMD_TEMP
endif

digi_src := $(GOPATH)/src/digi.dev/digi
driver_dir := $(digi_src)/driver
driver_handler := $(WORKDIR)/$(IMAGE_DIR)/driver/*
digi_config := $(WORKDIR)/$(IMAGE_DIR)/deploy/*
build_dir := /tmp/digi-build-$(IMAGE_NAME)-$(NAME)

# model
.PHONY: init gen model all delete image list edit
# init configs
define model
group: $(GROUP)
version: $(VERSION)
kind: $(KIND)
endef
export model

init:
	cd $(WORKDIR) && mkdir $(IMAGE_DIR) >/dev/null 2>&1 || true && \
	echo "$$model" > $(IMAGE_DIR)/model.yaml
gen:
	cd $(WORKDIR) && REPO=$(DRIVER_REPO) python $(DIGIHOME)/gen.py $(IMAGE_DIR) \
	&& python $(DIGIHOME)/patch.py $(IMAGE_DIR)
model:
	cd $(WORKDIR)/$(IMAGE_DIR) && kubectl apply -f crd.yaml >/dev/null
all: | gen model
delete:
	cd $(WORKDIR)/$(IMAGE_DIR) >/dev/null 2>&1; kubectl delete -f crd.yaml 2>/dev/null || true
	rm -r $(WORKDIR)/$(IMAGE_DIR) >/dev/null 2>&1 || true
image:
	cd $(WORKDIR) && ls -d */* 2> /dev/null | grep "model.yaml" | xargs -I {} dirname {}
list:
	kubectl get deploy --no-headers -o custom-columns=":metadata.name" $(FLAG)
edit:
	kubectl edit $(PLURAL) $(NAME) 2>&1 || kubectl edit $(PLURAL).$(GROUP) $(NAME)

.PHONY: clean-test test
clean-test:
	kubectl delete $(PLURAL).$(GROUP) $(NAME) >/dev/null 2>&1 || true
test: | all clean-test
	kubectl apply -f $(WORKDIR)/$(KIND)/test/cr.yaml
	cd $(WORKDIR) && GROUP=$(GROUP) VERSION=$(VERSION) KIND=$(KIND) \
    PLURAL=$(PLURAL) NAME=$(NAME) NAMESPACE=$(NAMESPACE) \
    POOL_PROVIDER=none MOUNTER=$(MOUNTER) \
	python $(IMAGE_DIR)/driver/handler.py

# driver
.PHONY: prepare
prepare:
	rm -r $(build_dir) >/dev/null 2>&1 || true
	mkdir -p $(build_dir)/deploy/
	rsync -r $(driver_dir) $(build_dir)
	rsync -r $(driver_dir)/deploy $(build_dir) || true
	# app specific configs overwrite the generic ones
	rsync -r $(digi_config) $(build_dir)/deploy || true
	rsync -r $(driver_dir)/requirements.txt $(build_dir) || true

.PHONY: build
build: | prepare gen
	rsync $(driver_handler) $(build_dir)/ || true
	# use DOCKER_BUILDKIT=0 to enable more messages
	cd $(build_dir) && $(DOCKER_CMD) build -t $(DRIVER_REPO)/$(IMAGE_NAME):latest $(BUILDFLAG) -f deploy/image/Dockerfile . || true
	$(DOCKER_CMD) push $(DRIVER_REPO)/$(IMAGE_NAME):latest $(BUILDFLAG) || true
	rm -r $(build_dir) || true

# image
.PHONY: push pull
push:
	mkdir $(DIGI_REPO) >/dev/null 2>&1 || true
	cd $(WORKDIR) && tar czf $(IMAGE_NAME).gz $(IMAGE_DIR) && mv $(IMAGE_NAME).gz $(DIGI_REPO)/ >/dev/null || true
pull:
	cd $(WORKDIR) && rsync $(DIGI_REPO)/$(IMAGE_NAME).gz . && tar xzf $(IMAGE_NAME).gz && rm $(IMAGE_NAME).gz > /dev/null

# deploy
.PHONY: run stop watch
run: | prepare model
	# stop any existing: delete model, driver, pool
	helm list -q | grep $(NAME) >/dev/null 2>&1 && \
	((kubectl delete $(PLURAL) $(NAME) >/dev/null 2>&1 || \
	kubectl delete $(PLURAL).$(GROUP) $(NAME) >/dev/null 2>&1) || true) & \
	helm uninstall $(NAME) >/dev/null 2>&1 || true
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- zapi drop -f $(NAME) >/dev/null 2>&1 || true
	# deploy anew: create model, driver, pool
	# TBD make pool optional by checking values.yaml
	cd $(build_dir)/deploy && mv cr.yaml ./templates; \
	helm install -f values.yaml --set name=$(NAME) $(NAME) . >/dev/null && \
	(kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname`\
    -- zapi create $(NAME)) >/dev/null 2>&1
	rm -r $(build_dir) || true
stop:
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- zapi drop -f $(NAME) >/dev/null 2>&1 || true
	helm list -q | grep $(NAME) >/dev/null 2>&1 && \
	((kubectl delete $(PLURAL) $(NAME) >/dev/null 2>&1 || \
	kubectl delete $(PLURAL).$(GROUP) $(NAME) >/dev/null 2>&1) || true) & \
	helm uninstall $(NAME) >/dev/null 2>&1 && echo $(NAME) || echo "$(NAME) isn't running"

watch:
	# the former runs faster
	watch -n$(INTERVAL) -t "(kubectl get $(PLURAL) $(NAME) -oyaml 2>/dev/null \
 	|| kubectl get $(PLURAL).$(GROUP) $(NAME) -oyaml) | kubectl neat $(NEATLEVEL)"

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
	kubectl port-forward service/$(LAKE) 9867:6534 || true
# debug
.PHONY: log
log:
	kubectl logs `kubectl get pod --field-selector status.phase=Running \
	-l name=$(NAME) -oname --sort-by=.status.startTime | tail -n1 | sed "s/^.\{4\}//"`
# GC
.PHONY: gc
gc:
	crds=$$(kubectl get crds --no-headers -o custom-columns=":metadata.name"); \
	for i in $$crds; do \
	  	count=$$(kubectl get $$i -oname | wc -l); \
		if [[ $$count -eq 0 ]]; \
		 then kubectl delete crd $$i >/dev/null ; echo $$i; fi \
	done