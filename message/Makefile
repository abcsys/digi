PREREQUISITES = rpk emqx_ctl
K := $(foreach exec,$(PREREQUISITES),\
        $(if $(shell which $(exec)),,$(error "No $(exec) in PATH")))

.PHONY: redpanda rpk
rpk:
	brew install rpk
redpanda: | rpk

# TBD emqx_ctl
