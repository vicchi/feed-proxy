SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -O extglob -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

ifeq ($(.DEFAULT_GOAL),)
ifneq ($(shell test -f .env; echo $$?), 0)
$(error Cannot find a .env file; copy .env.sample and customise)
endif
endif

# Wrap the build in a check for an existing .env file
ifeq ($(shell test -f .env; echo $$?), 0)
include .env
ENVVARS := $(shell sed -ne 's/ *\#.*$$//; /./ s/=.*$$// p' .env )
$(foreach var,$(ENVVARS),$(eval $(shell echo export $(var)="$($(var))")))

.DEFAULT_GOAL := help

VERSION := $(shell cat ./VERSION)
COMMIT_HASH := $(shell git log -1 --pretty=format:"sha-%h")
PLATFORMS := "linux/arm/v7,linux/arm64/v8,linux/amd64"

BUILD_FLAGS ?= 

FEEDPROXY := feed-proxy
FEEDPROXY_BUILDER := $(FEEDPROXY)-builder
FEEDPROXY_USER := vicchi
FEEDPROXY_REPO := ${GITHUB_REGISTRY}/${FEEDPROXY_USER}
FEEDPROXY_IMAGE := ${FEEDPROXY}
FEEDPROXY_DOCKERFILE := ./docker/${FEEDPROXY}/Dockerfile

HADOLINT_IMAGE := hadolint/hadolint

.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' Makefile

# .PHONY: lint
# lint: lint-dockerfiles	## Run all linters on the code base

# .PHONY: lint-dockerfiles
# .PHONY: _lint-dockerfiles ## Lint all Dockerfiles
# lint-dockerfiles: lint-${FEEDPROXY}-dockerfile

# .PHONY: lint-${FEEDPROXY}-dockerfile
# lint-${FEEDPROXY}-dockerfile:
# 	$(MAKE) _lint_dockerfile -e BUILD_DOCKERFILE="${FEEDPROXY_DOCKERFILE}"

.PHONY: lint
lint: lint-pylint lint-flake8 lint-mypy lint-docker	## Run all linters on the code base

.PHONY: lint-pylint
lint-pylint:	## Run pylint on the code base
	pylint --verbose -j 4 --reports yes --recursive yes feed_proxy tools *.py

.PHONY: lint-flake8
lint-flake8:	## Run flake8 on the code base
	flake8 -j 4 feed_proxy tools *.py

.PHONY: lint-mypy
lint-mypy:	## Run flake8 on the code base
	mypy feed_proxy tools *.py

.PHONY: lint-docker
lint-docker: lint-compose lint-dockerfiles ## Lint all Docker related files

.PHONY: lint-compose
lint-compose:	## Lint docker-compose.yml
	docker compose -f docker-compose.yml config 1> /dev/null
	docker compose -f docker-compose.local.yml config 1> /dev/null

.PHONY: lint-dockerfiles
lint-dockerfiles: _lint-dockerfiles ## Lint all Dockerfiles
.PHONY: _lint-dockerfiles
_lint-dockerfiles: lint-${FEEDPROXY}-dockerfile

.PHONY: lint-${FEEDPROXY}-dockerfile
lint-${FEEDPROXY}-dockerfile:
	$(MAKE) _lint_dockerfile -e BUILD_DOCKERFILE="${FEEDPROXY_DOCKERFILE}"

BUILD_TARGETS := build_feedproxy

.PHONY: build
build: $(BUILD_TARGETS) ## Build all images

REBUILD_TARGETS := rebuild_feedproxy

.PHONY: rebuild
rebuild: $(REBUILD_TARGETS) ## Rebuild all images (no cache)

# feedproxy targets

build_feedproxy:	repo_login	## Build the feedproxy image
	$(MAKE) _build_image \
		-e BUILD_DOCKERFILE=./docker/$(FEEDPROXY)/Dockerfile \
		-e BUILD_IMAGE=$(FEEDPROXY_IMAGE)

rebuild_feedproxy:	## Rebuild the feedproxy image (no cache)
	$(MAKE) _build_image \
		-e BUILD_DOCKERFILE=./docker/$(FEEDPROXY)/Dockerfile \
		-e BUILD_IMAGE=$(FEEDPROXY_IMAGE) \
		-e BUILD_FLAGS="--no-cache"

.PHONY: _lint_dockerfile
_lint_dockerfile:
	docker run --rm -i -e HADOLINT_IGNORE=DL3008,DL3018,DL3003 ${HADOLINT_IMAGE} < ${BUILD_DOCKERFILE}

.PHONY: _build_image
_build_image:
	docker buildx inspect $(FEEDPROXY_BUILDER) > /dev/null 2>&1 || \
		docker buildx create --name $(FEEDPROXY_BUILDER) --bootstrap --use
	docker buildx build --platform=$(PLATFORMS) \
		--file ${BUILD_DOCKERFILE} --push \
		--tag ${FEEDPROXY_REPO}/${BUILD_IMAGE}:latest \
		--tag ${FEEDPROXY_REPO}/${BUILD_IMAGE}:$(VERSION) \
		--tag ${FEEDPROXY_REPO}/${BUILD_IMAGE}:$(COMMIT_HASH) \
		$(BUILD_FLAGS) \
		--ssh default $(BUILD_FLAGS) .

.PHONY: repo_login
repo_login:
	echo "${GITHUB_PAT}" | docker login ${GITHUB_REGISTRY} -u ${GITHUB_USER} --password-stdin

# No .env file; fail the build
else
.DEFAULT:
	$(error Cannot find a .env file; copy .env.sample and customise)
endif
