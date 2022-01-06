ifndef DIGIHOME
override DIGIHOME = ~/.digi
endif

ifndef WORKDIR
override WORKDIR = .
endif

ifndef DIGI_REPO
override DIGI_REPO = ~/.digi/profiles
endif

ifndef PROFILE_NAME
override PROFILE_NAME = $(KIND).$(VERSION).$(GROUP)
endif

ifndef DRIVER_REPO
override DRIVER_REPO = DRIVER_REPO_TEMP
endif

ifndef DOCKER_CMD
override DOCKER_CMD = DOCKER_CMD_TEMP
endif

digi_src := $(GOPATH)/src/digi.dev/digi
driver_dir := $(digi_src)/driver
driver_handler := $(WORKDIR)/$(PROFILE)/driver/*
digi_config := $(WORKDIR)/$(PROFILE)/deploy/*
build_dir := /tmp/digi-build-$(PROFILE_NAME)-$(NAME)

# model
.PHONY: init gen model all delete profile proflie-local list
# init configs
define model
group: $(GROUP)
version: $(VERSION)
kind: $(KIND)
endef
export model

init:
	cd $(WORKDIR) && mkdir $(PROFILE) >/dev/null 2>&1 || true && \
	echo "$$model" > $(PROFILE)/model.yaml
gen:
	cd $(WORKDIR) && REPO=$(DRIVER_REPO) python $(DIGIHOME)/gen.py $(PROFILE) \
	&& python $(DIGIHOME)/patch.py $(PROFILE)
model:
	cd $(WORKDIR)/$(PROFILE) && kubectl apply -f crd.yaml >/dev/null
all: | gen model
delete:
	cd $(WORKDIR)/$(PROFILE) >/dev/null 2>&1; kubectl delete -f crd.yaml 2>/dev/null || true
	rm -r $(WORKDIR)/$(PROFILE) >/dev/null 2>&1 || true
profile:
	cd $(WORKDIR) && ls -d */* 2> /dev/null | grep "model.yaml" | xargs -I {} dirname {}
profile-local:
	cd $(DIGI_REPO) && ls 2> /dev/null
list:
	kubectl get deploy --no-headers -o custom-columns=":metadata.name" $(FLAG)

.PHONY: edit edit-all
edit:
	(kubectl get $(PLURAL) $(NAME) -oyaml 2>/dev/null \
    || kubectl get $(PLURAL).$(GROUP) $(NAME) -oyaml) | kubectl neat -l 0 \
    > $(FILE) && vi $(FILE) && kubectl apply -f $(FILE); rm $(FILE)
edit-all:
	kubectl edit $(PLURAL) $(NAME) 2>&1 || kubectl edit $(PLURAL).$(GROUP) $(NAME)

.PHONY: clean-test test
clean-test:
	kubectl delete $(PLURAL).$(GROUP) $(NAME) >/dev/null 2>&1 || true
test: | all clean-test
	kubectl apply -f $(WORKDIR)/$(KIND)/test/cr.yaml
	cd $(WORKDIR) && GROUP=$(GROUP) VERSION=$(VERSION) KIND=$(KIND) \
    PLURAL=$(PLURAL) NAME=$(NAME) NAMESPACE=$(NAMESPACE) \
    POOL_PROVIDER=none MOUNTER=$(MOUNTER) \
	python $(PROFILE)/driver/handler.py
	# TBD allow using pool

# driver
.PHONY: prepare
prepare:
	rm -r $(build_dir) >/dev/null 2>&1 || true
	mkdir -p $(build_dir)/deploy/
	rsync -r $(driver_dir) $(build_dir)
	rsync -r $(driver_dir)/deploy $(build_dir) || true
	# app specific configs overwrite the generic ones
	rsync -r $(digi_config) $(build_dir)/deploy || true

.PHONY: build
build: | prepare gen
	rsync $(driver_handler) $(build_dir)/ || true
	# use DOCKER_BUILDKIT=0 to enable more messages
	cd $(build_dir) && $(DOCKER_CMD) build -t $(DRIVER_REPO)/$(PROFILE_NAME):latest $(BUILDFLAG) -f deploy/image/Dockerfile . || true
	$(DOCKER_CMD) push $(DRIVER_REPO)/$(PROFILE_NAME):latest $(PUSHFLAG) || true
	rm -r $(build_dir) || true

# digi profiles
.PHONY: push pull
push:
	mkdir $(DIGI_REPO) >/dev/null 2>&1 || true
	cd $(WORKDIR) && tar czf $(PROFILE_NAME).gz $(PROFILE) && mv $(PROFILE_NAME).gz $(DIGI_REPO)/ >/dev/null || true
pull:
	cd $(WORKDIR) && rsync $(DIGI_REPO)/$(PROFILE_NAME)*.gz . && tar xzf $(PROFILE_NAME)*.gz && rm $(PROFILE_NAME)*.gz > /dev/null

# deploy
.PHONY: run stop
run: | prepare model
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- zed drop -f $(NAME) >/dev/null 2>&1 || true
	# TBD make pool optional by checking values.yaml
	cd $(build_dir)/deploy && mv cr.yaml ./templates; \
	helm template -f values.yaml --set name=$(NAME) $(RUNFLAG) $(NAME) . > run.yaml && \
	kubectl delete -f run.yaml >/dev/null 2>&1 || true && \
	kubectl apply -f run.yaml >/dev/null && \
	(kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname`\
    -- zed create $(NAME)) >/dev/null && echo $(NAME)
	rm -r $(build_dir) || true
stop:
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- zed drop -f $(NAME) >/dev/null || true
	kubectl delete serviceaccount $(NAME) >/dev/null || true & \
	kubectl delete clusterrole $(NAME) >/dev/null || true & \
	kubectl delete clusterrolebinding $(NAME) >/dev/null || true & \
	kubectl delete service $(NAME) >/dev/null || true & \
	((kubectl delete $(PLURAL) $(NAME) >/dev/null || \
	kubectl delete $(PLURAL).$(GROUP) $(NAME)) >/dev/null || true) & \
	kubectl delete deployment $(NAME) >/dev/null && \
	echo $(NAME) || echo "$(NAME) isn't running"

.PHONY: check watch
check:
	(kubectl get $(PLURAL) $(NAME) -oyaml 2>/dev/null \
 	|| kubectl get $(PLURAL).$(GROUP) $(NAME) -oyaml) | kubectl neat $(NEATLEVEL)
watch:
	watch -n$(INTERVAL) -t "(kubectl get $(PLURAL) $(NAME) -oyaml 2>/dev/null \
 	|| kubectl get $(PLURAL).$(GROUP) $(NAME) -oyaml) | kubectl neat $(NEATLEVEL)"

# lake
ifndef LAKENAME
override LAKENAME = lake
endif
.PHONY: query connect-lake
# TBD enforce single lake or use service to identify lake
query:
	kubectl exec -it `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
        -- zed query $(FLAG) "$(QUERY)"
connect-lake:
	kubectl port-forward service/$(LAKENAME) 9867:6534 || true

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

# Visualization
ifndef LOCALPORT
override LOCALPORT = 7534
endif
.PHONY: viz viz-space
viz:
	echo 127.0.0.1:$(LOCALPORT)
	kubectl port-forward service/$(NAME) $(LOCALPORT):7534 >/dev/null || true
viz-space:
	echo TBD digiboard
