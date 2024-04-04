#                                                                               
# Commonly used targets (see each target for more information):                 
#   run: Build code.                                                            

SHELL := /usr/bin/env bash                                                      
PYLINT_OPTS="C0114,C0116,C0115,W0719,R0903,W0718,C0413,C0411,C0209,R0915,R0801"
VERSION=0.1.0
IMAGE=migrx/projectset-app

.PHONY: all
all: help

.PHONY: help
help:
	@echo "make tests - run tests"
	@echo "make run - run"

.PHONY: run
run:
	PORT=8082 PYENV=${PYENV} ./start

.PHONY: tests
tests:
	find . -type f -name "*.py" |xargs ${PYENV}/python3 -m yapf -i
	find . -type f -name "*.py" |xargs ${PYENV}/python3 -m pylint --unsafe-load-any-extension=y --disable ${PYLINT_OPTS}

.PHONY: docker-build
docker-build:
	docker build -t ${IMAGE}:${VERSION} .

.PHONY: docker-push
docker-push:
	docker push ${IMAGE}:${VERSION}

PLATFORMS ?= linux/arm64,linux/amd64,linux/s390x,linux/ppc64le                     
.PHONY: docker-buildx                                                              
docker-buildx:
	sed -e '1 s/\(^FROM\)/FROM --platform=\$$\{BUILDPLATFORM\}/; t' -e ' 1,// s//FROM --platform=\$$\{BUILDPLATFORM\}/' Dockerfile > Dockerfile.cross
	docker buildx create --name project-v3-builder                    
	docker buildx use project-v3-builder                                
	docker buildx build --push --platform=$(PLATFORMS) --tag ${IMAGE}:${VERSION} -f Dockerfile.cross .
	docker buildx rm project-v3-builder
	rm Dockerfile.cross     
