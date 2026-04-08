# Makefile — CodeCannon project-specific targets
#
# Workflow targets (branch, pr, abandon, merge, promote) come from Makefile.agents.mk.
# This file adds CodeCannon-specific targets: sync, versioning, and deployment.

INTEGRATION_BRANCH = dev
include Makefile.agents.mk

.DEFAULT_GOAL := help
.PHONY: help check dev sync bump-patch bump-minor bump-major set-version deploy-preview deploy-prod

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Sync"
	@echo "  check            Validate skill placeholders against config"
	@echo "  dev              Preview sync output (dry run)"
	@echo "  sync             Regenerate adapter output from skills/"
	@echo ""
	@echo "Git workflow (from Makefile.agents.mk)"
	@echo "  branch name=X    Create feature branch from $(INTEGRATION_BRANCH)"
	@echo "  pr               Push and open PR targeting $(INTEGRATION_BRANCH)"
	@echo "  merge            Merge current PR into $(INTEGRATION_BRANCH)"
	@echo "  abandon          Discard changes and delete current feature branch"
	@echo ""
	@echo "Versioning"
	@echo "  bump-patch       Bump patch (X.Y.Z+1), commit, and tag"
	@echo "  bump-minor       Bump minor (X.Y+1.0), commit, and tag"
	@echo "  bump-major       Bump major (X+1.0.0), commit, and tag"
	@echo "  set-version V=X  Set explicit version, commit, and tag"
	@echo ""
	@echo "Deployment"
	@echo "  deploy-preview   Push $(INTEGRATION_BRANCH) for preview/testing"
	@echo "  deploy-prod      Push $(PRODUCTION_BRANCH) with tags"

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
	git commit -S -m "Bump version to $$new"; \
	git tag -s v$$new -m "v$$new"

# Bump the minor segment (X.Y.Z → X.Y+1.0), commit, and tag.
bump-minor:
	@v=$$(cat VERSION); \
	major=$$(echo $$v | awk -F. '{print $$1}'); \
	minor=$$(echo $$v | awk -F. '{print $$2}'); \
	new="$$major.$$((minor + 1)).0"; \
	echo $$new > VERSION; \
	git add VERSION; \
	git commit -S -m "Bump version to $$new"; \
	git tag -s v$$new -m "v$$new"

# Bump the major segment (X.Y.Z → X+1.0.0), commit, and tag.
bump-major:
	@v=$$(cat VERSION); \
	major=$$(echo $$v | awk -F. '{print $$1}'); \
	new="$$((major + 1)).0.0"; \
	echo $$new > VERSION; \
	git add VERSION; \
	git commit -S -m "Bump version to $$new"; \
	git tag -s v$$new -m "v$$new"

# Set an explicit version. Usage: make set-version V=1.2.3
set-version:
ifndef V
	$(error Usage: make set-version V=<version>)
endif
	echo $(V) > VERSION
	git add VERSION
	git commit -S -m "Bump version to $(V)"
	git tag -s v$(V) -m "v$(V)"

# Push the integration branch for preview/testing.
deploy-preview:
	git checkout $(INTEGRATION_BRANCH)
	git pull --rebase origin $(INTEGRATION_BRANCH)
	git push origin $(INTEGRATION_BRANCH)

# Publish a tagged release to production.
deploy-prod:
	git checkout $(PRODUCTION_BRANCH)
	git pull --rebase origin $(PRODUCTION_BRANCH) --tags
	git push origin $(PRODUCTION_BRANCH) --tags
