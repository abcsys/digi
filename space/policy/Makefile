REPO=silveryfu
IMAGE=policer:latest

.PHONY: api build
api:
	operator-sdk add api --api-version=digi.dev/v1 --kind=$(API)
	operator-sdk add controller --api-version=digi.dev/v1 --kind=$(API)
build:
	operator-sdk generate k8s || exit 1
	operator-sdk generate crds || exit 1

	docker login
	operator-sdk build $(REPO)/$(IMAGE)
	docker push $(REPO)/$(IMAGE)
	sed -e 's/{{REPO}}/$(REPO)/g' ./deploy/actor.template > ./deploy/actor.yaml

.PHONY: stop run mock test
stop:
	kubectl delete -f deploy/crds/ || true
	kubectl delete -f deploy/ || true
run: | stop
	kubectl create -f deploy/crds/
	kubectl create -f deploy/
mock:
	kubectl apply -f deploy/mocks/crds/ || true
	kubectl apply -f deploy/mocks/crs/ || true
test: | run mock
	$(info test on mocks)

.PHONY: log all
log:
	kubectl logs $(shell kubectl get pods --selector=name=policer -o jsonpath="{.items[*].metadata.name}")
all: | build test
	$(info build and run)
