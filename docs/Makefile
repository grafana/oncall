IMAGE = grafana/docs-base:latest
CONTENT_PATH = /hugo/content/docs/oncall/latest
PORT = 3002:3002

.PHONY: pull
pull:
	docker pull $(IMAGE)

.PHONY: docs
docs: pull
	docker run -v '$(shell pwd)/sources:$(CONTENT_PATH):Z' -p $(PORT) --rm -it $(IMAGE)
