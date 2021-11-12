.PHONY: dist
dist:
	python setup.py sdist bdist_wheel && twine upload --skip-existing dist/*

.PHONY: test build deploy template all
g:="mock.digi.dev"
v:="v1"
r:="samples"
n:="sample"
ns:="default"

# local tests
test:
	GROUP=$(g) VERSION=$(v) PLURAL=$(r) NAME=$(n) NAMESPACE=$(ns) python digi
build:
	docker build -t silveryfu/sample:latest -f deploy/image/Dockerfile .
	docker push silveryfu/sample:latest
deploy:
	cd deploy; helm install -f values.yaml $(n) .
template:
	cd deploy; helm template .
all: | build deploy
	$(info build and deploy)

.PHONY: test_mt clean
test_mt:
	python digi/tests/mount_test.py
