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
override DRIVER_REPO = REPO_TEMP
endif

ifndef DOCKER_CMD
override DOCKER_CMD = CMD_TEMP
endif

ifndef CR
override CR = cr.yaml
endif


digi_src := $(GOPATH)/src/digi.dev/digi
driver_dir := $(digi_src)/driver
driver_handler := $(WORKDIR)/$(PROFILE)/driver/*
digi_config := $(WORKDIR)/$(PROFILE)/deploy/*
build_dir := /tmp/digi-build-$(PROFILE_NAME)-$(NAME)

# model
.PHONY: init gen model all delete delete-all profile proflie-local list
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
	cd $(WORKDIR) && DRIVER_REPO=$(DRIVER_REPO) $(GENFLAG) python $(DIGIHOME)/gen.py $(PROFILE) \
	&& python $(DIGIHOME)/patch.py $(PROFILE)
model:
	cd $(WORKDIR)/$(PROFILE) && kubectl apply -f crd.yaml >/dev/null
all: | gen model
delete:
	rm -r $(WORKDIR)/$(PROFILE) >/dev/null && echo $(PROFILE) || echo "unable to delete $(PROFILE)"; exit
delete-all: | delete
	cd $(WORKDIR)/$(PROFILE) >/dev/null 2>&1; kubectl delete -f crd.yaml 2>/dev/null || true
profile:
	cd $(WORKDIR) && ls -d */* 2> /dev/null | grep "model.yaml" | xargs -I {} dirname {}
profile-local:
	cd $(DIGI_REPO) && ls 2> /dev/null
list:
	kubectl get deploy --no-headers -o custom-columns=":metadata.name" $(FLAG)

.PHONY: edit edit-all
edit:
	# TBD add revision number in the temporary file
	(kubectl get $(PLURAL) $(NAME) -oyaml 2>/dev/null \
    || kubectl get $(PLURAL).$(VERSION).$(GROUP) $(NAME) -oyaml) | neat -l 0 \
    > $(FILE) && vi $(FILE) && kubectl apply -f $(FILE); rm $(FILE)
edit-all:
	kubectl edit $(PLURAL) $(NAME) 2>&1 || kubectl edit $(PLURAL).$(GROUP) $(NAME)

.PHONY: clean-test test
clean-test:
	kubectl delete $(PLURAL).$(VERSION).$(GROUP) $(NAME) >/dev/null 2>&1 || true
test: | all clean-test
	kubectl apply -f $(WORKDIR)/$(KIND)/test/cr.yaml
	cd $(WORKDIR) && GROUP=$(GROUP) VERSION=$(VERSION) KIND=$(KIND) \
    PLURAL=$(PLURAL) NAME=$(NAME) NAMESPACE=$(NAMESPACE) \
    POOL_PROVIDER=none MOUNTER=$(MOUNTER) \
	python $(PROFILE)/driver/handler.py
	# TBD allow using pool

# driver
.PHONY: prepare-build-dir prepare-build prepare-deploy prepare
prepare-build-dir:
	rm -r $(build_dir) >/dev/null 2>&1 || true
	mkdir -p $(build_dir)/deploy/
prepare-build:
	rsync -r $(driver_dir) $(build_dir)
	rsync $(driver_dir)/digi/handler.py $(build_dir)/
	rsync $(driver_dir)/digi/visual.py $(build_dir)/
prepare-deploy:
	rsync -r $(driver_dir)/deploy $(build_dir) || true
	# app specific configs overwrite the generic ones
	rsync -r $(digi_config) $(build_dir)/deploy || true
prepare: | prepare-build-dir prepare-build prepare-deploy

.PHONY: build clear-manifest
ifndef ARCH
override ARCH = ARCH_TEMP
endif
ifndef TAG
override TAG = latest
endif
build: | gen prepare
	# use DOCKER_BUILDKIT=0 to enable more messages
	rsync $(driver_handler) $(build_dir)/ || true
	cd $(build_dir) && $(DOCKER_CMD) buildx build -t $(DRIVER_REPO)/$(PROFILE_NAME):$(ARCH) $(BUILDFLAG) -f deploy/image/Dockerfile . || true
	$(DOCKER_CMD) push $(DRIVER_REPO)/$(PROFILE_NAME):$(ARCH) $(PUSHFLAG) || true
	rm -r $(build_dir) || true

	$(DOCKER_CMD) manifest create $(DRIVER_REPO)/$(PROFILE_NAME):$(TAG) \
	--amend $(DRIVER_REPO)/$(PROFILE_NAME):$(ARCH)
	$(DOCKER_CMD) manifest push $(DRIVER_REPO)/$(PROFILE_NAME):$(TAG)
clear-manifest:
	$(DOCKER_CMD) manifest rm $(DRIVER_REPO)/$(PROFILE_NAME):$(TAG) >/dev/null 2>&1 || true

# digi profiles
.PHONY: push pull
push:
	mkdir $(DIGI_REPO) >/dev/null 2>&1 || true
	cd $(WORKDIR) && tar czf $(PROFILE_NAME).gz $(PROFILE) && mv $(PROFILE_NAME).gz $(DIGI_REPO)/ >/dev/null || true
pull:
	cd $(WORKDIR) && rsync $(DIGI_REPO)/$(PROFILE_NAME)*.gz . && tar xzf $(PROFILE_NAME)*.gz && rm $(PROFILE_NAME)*.gz > /dev/null

#commit and recreate helpers
commit:
	echo $(NAME)
	rm -rf $(WORKDIR)/$(NAME)_snapshot
	rm -f $(WORKDIR)/$(NAME)_snapshot.zip
	cp -r $(WORKDIR)/$(KIND) $(WORKDIR)/$(NAME)_snapshot
	digi check $(NAME) > curr_branches.yaml
	mv curr_branches.yaml $(WORKDIR)/$(NAME)_snapshot
	mkdir $(WORKDIR)/$(NAME)_snapshot/records
	python $(DIGIHOME)/helper.py "save" $(WORKDIR)/$(NAME)_snapshot $(NAME)
	kubectl get $(PLURAL).$(VERSION).$(GROUP) $(NAME) -oyaml | kubectl neat -l 0 > intent_status.yaml
	mv intent_status.yaml $(WORKDIR)/$(NAME)_snapshot
recreate-tail:
	cp $(WORKDIR)/$(DIRNAME)/intent_status.yaml $(WORKDIR)/$(DIRNAME)/temp.yaml
	python $(DIGIHOME)/helper.py "edit" $(WORKDIR) $(DIRNAME) $(NAME)
	kubectl apply -f $(WORKDIR)/$(DIRNAME)/temp.yaml
	rm $(WORKDIR)/$(DIRNAME)/temp.yaml	
	python $(DIGIHOME)/helper.py "load" $(WORKDIR) $(DIRNAME) $(NAME)

# deploy
.PHONY: run stop run-no-pool
run: | prepare model
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- bash -c "zed drop -f $(NAME) >/dev/null 2>&1" || true
	cd $(build_dir)/deploy && mv $(CR) ./templates; \
	helm template -f values.yaml --set name=$(NAME) $(RUNFLAG) $(NAME) . > run.yaml && \
	kubectl delete -f run.yaml >/dev/null 2>&1 || true && \
	kubectl apply -f run.yaml >/dev/null || (echo "unable to run $(NAME), check $(CR)"; exit 1) && \
	(kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- bash -c "zed create $(NAME)") >/dev/null && echo $(NAME) || echo "unable to create pool $(NAME)"
	rm -rf $(build_dir)
stop:
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- bash -c "zed drop -f $(NAME) >/dev/null" || true
	kubectl delete serviceaccount $(NAME) >/dev/null || true & \
	kubectl delete clusterrole $(NAME) >/dev/null || true & \
	kubectl delete clusterrolebinding $(NAME) >/dev/null || true & \
	kubectl delete service $(NAME) >/dev/null || true & \
	((kubectl delete $(PLURAL) $(NAME) >/dev/null || \
	kubectl delete $(PLURAL).$(VERSION).$(GROUP) $(NAME)) >/dev/null || true) & \
	kubectl delete deployment $(NAME) >/dev/null && \
	echo $(NAME) || echo "$(NAME) isn't running"
run-no-pool: | prepare model
	cd $(build_dir)/deploy && mv $(CR) ./templates; \
	helm template -f values.yaml --set name=$(NAME) --set pool_provider=none $(RUNFLAG) $(NAME) . > run.yaml && \
	kubectl delete -f run.yaml >/dev/null 2>&1 || true && \
	kubectl apply -f run.yaml >/dev/null && echo $(NAME) || \
    echo "unable to run $(NAME)"
	rm -r $(build_dir) || true

.PHONY: check watch
check:
	(kubectl get $(PLURAL) $(NAME) -oyaml 2>/dev/null \
 	|| kubectl get $(PLURAL).$(VERSION).$(GROUP) $(NAME) -oyaml) | neat $(NEATLEVEL)
watch:
	watch -n$(INTERVAL) -t "(kubectl get $(PLURAL) $(NAME) -oyaml 2>/dev/null \
 	|| kubectl get $(PLURAL).$(VERSION).$(GROUP) $(NAME) -oyaml) | neat $(NEATLEVEL)"

ifndef SHELL_BIN
override SHELL_BIN = sh
endif
.PHONY: connect
connect:
	kubectl exec -it `kubectl get pod --field-selector status.phase=Running -l name=$(NAME) -oname` -- /bin/$(SHELL_BIN)

# lake
ifndef LAKENAME
override LAKENAME = lake
endif
.PHONY: query connect-lake start-lake stop-lake load
# TBD enforce single lake or use service to identify lake
query:
	kubectl exec -it `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
        -- bash -c "$(FLAG) zed query $(ZEDFLAG) '$(QUERY)'"
connect-lake:
	kubectl port-forward service/$(LAKENAME) 9867:6534 || true
start-lake:
	WORKDIR=$(DIGIHOME) digi run lake lake --no-pool
stop-lake:
	digi stop lake
load:
	cd $(WORKDIR) && zed load -use $(NAME) $(FILE)

# syncer
.PHONY: start-syncer stop-syncer
start-syncer:
 	# force restart syncer
	cd $(DIGIHOME)/space/sync && \
	kubectl delete -f deploy/ >/dev/null 2>&1 || true && \
	kubectl apply -f deploy/crds/ >/dev/null && \
	kubectl apply -f deploy/ >/dev/null && echo syncer
stop-syncer:
	cd $(DIGIHOME)/space/sync && \
 	kubectl delete -f deploy/crds/ >/dev/null && \
	kubectl delete -f deploy/ >/dev/null && echo syncer

# TBD global mounter

# message/emqx
.PHONY: start-emqx stop-emqx
start-emqx:
	WORKDIR=$(DIGIHOME) digi run message/emqx emqx
stop-emqx:
	digi stop emqx

.PHONY: start-space stop-space
start-space: | start-lake # ...
stop-space: | stop-lake
.PHONY: list-space switch-space rename-space show-space
list-space:
	ctx $(FLAG)
switch-space:
	ctx $(NAME) > /dev/null 2>&1 && echo "Switched to space $(NAME)" || echo "Unable to switch to space $(NAME)"
rename-space:
	kubectl config rename-context $(OLD_NAME) $(NAME) >/dev/null \
	&& echo "Space $(OLD_NAME) renamed to $(NAME)"
ifndef SPACE
override SPACE = `ctx -c`
endif
show-space:
	ctx $(SPACE) > /dev/null
	# XXX fix auto-switch space after show
	printf "Apiserver:\n"
	kubectl cluster-info | grep Kubernetes | cut -d " " -f 7
	# TBD layered information
	echo "---"
	digi list -aq

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
	open http://127.0.0.1:$(LOCALPORT) >/dev/null 2>&1 || true
	kubectl port-forward service/$(NAME) $(LOCALPORT):7534 >/dev/null && (echo "unable to viz $(NAME), $(NAME) likely run without -v flag"; exit 1)
viz-space:
	echo TBD digiboard

.PHONY: view
view:
	WORKDIR=$(DIGIHOME) digi run view $(NAME)-view --no-pool
