build-JobCreationFunction:
	mkdir -p "$(ARTIFACTS_DIR)"
	python -m pip install pipenv
	pipenv lock -r > "$(ARTIFACTS_DIR)/requirements.txt"
	python -m pip install -r "$(ARTIFACTS_DIR)/requirements.txt" -t "$(ARTIFACTS_DIR)"
	cp -r core "$(ARTIFACTS_DIR)"
	cp lambdas/*.py "$(ARTIFACTS_DIR)"

build-CronSchedulerFunction:
	mkdir -p "$(ARTIFACTS_DIR)"
	python -m pip install pipenv
	pipenv lock -r > "$(ARTIFACTS_DIR)/requirements.txt"
	python -m pip install -r "$(ARTIFACTS_DIR)/requirements.txt" -t "$(ARTIFACTS_DIR)"
	cp -r core "$(ARTIFACTS_DIR)"
	cp lambdas/*.py "$(ARTIFACTS_DIR)"
