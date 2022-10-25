# make install
# make build: build locally
# make test: run all tests
# make test-unit: just unit tests
# make test-e2e: just e2e tests

.PHONY: build install clean test test-unit test-e2e
os ?= $(shell uname -s | tr '[:upper:]' '[:lower:]')

SRC = $(shell find . -type f -name '*.go' -not -path "./vendor/*")

build: dist/neat
dist/neat: $(SRC)
	GOOS=$* go build -o dist/$(@F)

install:
	go install .

clean:
	rm -rf dist

test: test-unit test-e2e test-integration

test-unit:
	go test -v ./...

test-e2e: dist/kubectl-neat_$(os)
	bats ./test/e2e-cli.bats

test-integration: dist/kubectl-neat_$(os).tar.gz dist/kubectl-neat_$(os)*/kubectl-neat dist/checksums.txt
	bats ./test/e2e-kubectl.bats
	bats ./test/e2e-krew.bats