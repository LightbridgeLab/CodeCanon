include Makefile.agents.mk

.PHONY: check dev sync bump-patch bump-minor bump-major set-version deploy-preview deploy-prod

# Validate that all skill placeholders resolve against the config.
check:
	./sync.sh --validate

# Preview what sync would generate without writing any files.
dev:
	./sync.sh --dry-run

# Regenerate .claude/commands/ and other adapter output from skills/.
sync:
	./sync.sh

# Bump the patch segment (X.Y.Z → X.Y.Z+1), commit, and tag.
bump-patch:
	@v=$$(cat VERSION); \
	major=$$(echo $$v | awk -F. '{print $$1}'); \
	minor=$$(echo $$v | awk -F. '{print $$2}'); \
	patch=$$(echo $$v | awk -F. '{print $$3}'); \
	new="$$major.$$minor.$$((patch + 1))"; \
	echo $$new > VERSION; \
	git add VERSION; \
	git commit -m "Bump version to $$new"; \
	git tag v$$new

# Bump the minor segment (X.Y.Z → X.Y+1.0), commit, and tag.
bump-minor:
	@v=$$(cat VERSION); \
	major=$$(echo $$v | awk -F. '{print $$1}'); \
	minor=$$(echo $$v | awk -F. '{print $$2}'); \
	new="$$major.$$((minor + 1)).0"; \
	echo $$new > VERSION; \
	git add VERSION; \
	git commit -m "Bump version to $$new"; \
	git tag v$$new

# Bump the major segment (X.Y.Z → X+1.0.0), commit, and tag.
bump-major:
	@v=$$(cat VERSION); \
	major=$$(echo $$v | awk -F. '{print $$1}'); \
	new="$$((major + 1)).0.0"; \
	echo $$new > VERSION; \
	git add VERSION; \
	git commit -m "Bump version to $$new"; \
	git tag v$$new

# Set an explicit version. Usage: make set-version V=1.2.3
set-version:
ifndef V
	$(error Usage: make set-version V=<version>)
endif
	echo $(V) > VERSION
	git add VERSION
	git commit -m "Bump version to $(V)"
	git tag v$(V)

# Publish the integration branch so consumers can pick up changes via submodule update.
deploy-preview:
	git push origin development

# Publish a tagged release to main.
deploy-prod:
	git push origin main --tags
