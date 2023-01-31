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

ifndef DRIVER_TAG
override DRIVER_TAG = latest
endif

ifndef DOCKER_CMD
override DOCKER_CMD = CMD_TEMP
endif

ifndef CR
override CR = cr.yaml
endif

ifndef DOCKERFILE
override DOCKERFILE = deploy/image/Dockerfile
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
	cd $(WORKDIR) && DRIVER_TAG=$(DRIVER_TAG) DRIVER_REPO=$(DRIVER_REPO) $(GENFLAG) python $(DIGIHOME)/gen.py $(PROFILE) \
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

.PHONY: clean-test start-test test
clean-test: delete-pool conn-lake-stop
	kubectl delete $(PLURAL).$(VERSION).$(GROUP) $(NAME) >/dev/null 2>&1 || true
start-test: | all conn-lake-bg
	kubectl apply -f $(WORKDIR)/$(KIND)/test/cr.yaml && \
	(kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- bash -c "zed create $(NAME)") >/dev/null && echo $(NAME) || (echo "unable to create pool $(NAME); is lake running?"; exit 1) && \
	cd $(WORKDIR) && GROUP=$(GROUP) VERSION=$(VERSION) KIND=$(KIND) \
    PLURAL=$(PLURAL) NAME=$(NAME) NAMESPACE=$(NAMESPACE) MOUNTER=$(MOUNTER) LAKE_PROVIDER=zed \
	python $(PROFILE)/driver/handler.py
test: | clean-test start-test clean-test

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
build: | gen prepare
	# use DOCKER_BUILDKIT=0 to enable more messages
	rsync $(driver_handler) $(build_dir)/ || true
	cd $(build_dir) && $(DOCKER_CMD) buildx build -t $(DRIVER_REPO)/$(PROFILE_NAME):$(ARCH) $(BUILDFLAG) -f $(DOCKERFILE) . || true
	$(DOCKER_CMD) push $(DRIVER_REPO)/$(PROFILE_NAME):$(ARCH) $(PUSHFLAG) || true
	rm -r $(build_dir) || true

	$(DOCKER_CMD) manifest create $(DRIVER_REPO)/$(PROFILE_NAME):$(DRIVER_TAG) \
	--amend $(DRIVER_REPO)/$(PROFILE_NAME):$(ARCH)
	$(DOCKER_CMD) manifest push $(DRIVER_REPO)/$(PROFILE_NAME):$(DRIVER_TAG)
clear-manifest:
	$(DOCKER_CMD) manifest rm $(DRIVER_REPO)/$(PROFILE_NAME):$(DRIVER_TAG) >/dev/null 2>&1 || true

# manage local digi profiles
.PHONY: push pull
push:
	mkdir $(DIGI_REPO) >/dev/null 2>&1 || true
	cd $(WORKDIR) && tar czf $(PROFILE_NAME).gz $(PROFILE) && mv $(PROFILE_NAME).gz $(DIGI_REPO)/ >/dev/null || true
pull:
	cd $(WORKDIR) && rsync $(DIGI_REPO)/$(PROFILE_NAME)*.gz . && tar xzf $(PROFILE_NAME)*.gz && rm $(PROFILE_NAME)*.gz > /dev/null

# commit
.PHONY: generation commit commit-inner recreate recreate-inner checksum-digi checksum-snapshot
generation:
	python $(DIGIHOME)/helper.py "generation" $(GROUP) $(VERSION) $(NAMESPACE) $(NAME) $(PLURAL)
# TBD improve and merge commands into the helper.py
commit: | conn-lake-bg commit-inner conn-lake-stop commit-recurse
commit-inner:
	mkdir -p $(WORKDIR)/$(TARGETDIR)
	rm -rf $(WORKDIR)/$(TARGETDIR)/$(NAME)_snapshot_gen$(GEN)
	# find the right kind and hande copying
	python $(DIGIHOME)/helper.py "find-kind" $(KIND) $(GROUP) $(NAME) $(WORKDIR) $(TARGETDIR) $(GEN) $(ADDPATHS)
	cp -r $(WORKDIR)/$(KIND) $(WORKDIR)/$(TARGETDIR)/$(NAME)_snapshot_gen$(GEN)
	# make a spec.yaml file in the snapshot directory to store the spec of the committed digi
	python $(DIGIHOME)/helper.py "make-spec" $(GROUP) $(VERSION) $(NAMESPACE) $(NAME) $(PLURAL) $(WORKDIR)/$(TARGETDIR)/$(NAME)_snapshot_gen$(GEN)
	# save branches
	mkdir -p $(WORKDIR)/$(TARGETDIR)/$(NAME)_snapshot_gen$(GEN)/records
	python $(DIGIHOME)/helper.py "save-branches" $(WORKDIR)/$(TARGETDIR)/$(NAME)_snapshot_gen$(GEN) $(NAME)
commit-recurse:
	# check for children
	python $(DIGIHOME)/helper.py "comm-hier" $(WORKDIR)/$(TARGETDIR)/$(NAME)_snapshot_gen$(GEN) $(NAME) $(TARGETDIR) $(GEN) $(ADDPATHS)
checksum-digi:
	python $(DIGIHOME)/helper.py "checksum-digi" $(GROUP) $(VERSION) $(NAMESPACE) $(NAME) $(PLURAL)
checksum-snapshot:
	python $(DIGIHOME)/helper.py "checksum-snapshot" $(WORKDIR) $(DIRNAME)
recreate: | conn-lake-bg recreate-inner conn-lake-stop
recreate-inner:
	cp $(WORKDIR)/$(DIRNAME)/spec.yaml $(WORKDIR)/$(DIRNAME)/temp_spec.yaml
	python $(DIGIHOME)/helper.py "remove-mount" $(WORKDIR) $(DIRNAME) $(NAME)
	python $(DIGIHOME)/helper.py "apply-spec" $(GROUP) $(VERSION) $(NAMESPACE) $(NAME) $(PLURAL) $(WORKDIR)/$(DIRNAME)/temp_spec.yaml
	rm $(WORKDIR)/$(DIRNAME)/temp_spec.yaml
	python $(DIGIHOME)/helper.py "load-branches" $(WORKDIR) $(DIRNAME) $(NAME)
	python $(DIGIHOME)/helper.py "rec-hier" $(WORKDIR) $(DIRNAME) $(SUFFIX) $(NAME)

# deploy
.PHONY: run stop run-no-pool
run: | prepare model delete-pool
	# TBD preflight check whether the lake is running
	cd $(build_dir)/deploy && mv $(CR) ./templates; \
	helm template -f values.yaml --set name=$(NAME) $(RUNFLAG) $(NAME) . > run.yaml && \
	kubectl delete -f run.yaml >/dev/null 2>&1 || true && \
	kubectl apply -f run.yaml >/dev/null || (echo "unable to run $(NAME), check $(CR)"; exit 1) && \
	(kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- bash -c "zed create $(NAME)") >/dev/null && echo $(NAME) || echo "unable to create pool $(NAME); is lake running?"
	rm -rf $(build_dir)
stop: | delete-pool
	kubectl delete pvc $(NAME) >/dev/null || true & \
	kubectl delete pv $(NAME) >/dev/null || true & \
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
	helm template -f values.yaml --set name=$(NAME) --set lake_provider=none $(RUNFLAG) $(NAME) . > run.yaml && \
	kubectl delete -f run.yaml >/dev/null 2>&1 || true && \
	kubectl apply -f run.yaml >/dev/null && echo $(NAME) || \
    echo "unable to run $(NAME)"
	rm -r $(build_dir) || true

.PHONY: check watch
check:
	(kubectl get $(PLURAL) $(NAME) -oyaml 2>/dev/null \
 	|| kubectl get $(PLURAL).$(VERSION).$(GROUP) $(NAME) -oyaml) | neat $(NEATLEVEL)
watch:
	watch -n$(INTERVAL) -t digi check $(NAME) -v $(NEATLEVEL)

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
.PHONY: query conn-lake conn-lake-bg conn-lake-stop start-lake stop-lake load
# TBD enforce single lake or use service to identify lake
query:
	kubectl exec -it `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
        -- bash -c "$(FLAG) zed query $(ZEDFLAG) '$(QUERY)'"
conn-lake: | conn-lake-stop
	kubectl port-forward service/$(LAKENAME) 9867:6534 || true
conn-lake-bg: | conn-lake-stop
	kubectl port-forward service/$(LAKENAME) 9867:6534 >/dev/null &
conn-lake-stop:
	kill $$(lsof -t -i:9867) >/dev/null 2>&1 || true && wait $$(lsof -t -i:9867) >/dev/null 2>&1
start-lake:
	WORKDIR=$(DIGIHOME) digi run lake lake --no-pool
stop-lake:
	digi stop lake
load:
	cd $(WORKDIR) && zed load -use $(NAME) $(FILE)
delete-pool:
	kubectl exec `kubectl get pod --field-selector status.phase=Running -l app=lake -oname` \
    -- bash -c "zed drop -f $(NAME) >/dev/null 2>&1" || true

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
.PHONY: register-space list-space switch-space rename-space show-space
register-space:
	./register-space.sh $(ADDR) $(USER) $(APISERVER) $(CONTEXT) $(CA.CRT) $(CLIENT.CRT) $(CLIENT.KEY)
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
