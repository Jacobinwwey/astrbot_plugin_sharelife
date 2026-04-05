docs-build:
	npm run docs:build --prefix docs

docs-build-github-pages:
	DOCS_BASE=/astrbot_plugin_sharelife/ npm run docs:build --prefix docs

docs-preview:
	npm run docs:preview --prefix docs

protocol-validate:
	python3 scripts/validate_protocol_examples.py

ops-validate:
	python3 scripts/validate_ops_assets.py

ops-smoke:
	bash scripts/smoke_observability_stack.sh

ops-smoke-raw:
	SHARELIFE_SMOKE_PRIVACY_MODE=off bash scripts/smoke_observability_stack.sh

ops-triage:
	python3 scripts/build_ops_smoke_triage.py --artifacts-dir output/ops-smoke --output output/ops-smoke/triage.md --json-output output/ops-smoke/triage.json

ops-annotate:
	python3 scripts/publish_ops_smoke_annotations.py --triage-json output/ops-smoke/triage.json

dx-scaffold:
	bash scripts/create-astrbot-plugin --name astrbot_plugin_demo --output output

dx-hot-reload:
	bash scripts/sharelife-hot-reload --watch . --cmd "python3 -m pytest -q tests/meta/test_dx_surface.py" --dry-run

dx-init-wizard:
	bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
