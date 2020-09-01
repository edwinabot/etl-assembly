build-JobCreationFunction:
	cp lambdas/job_creation.py "$(ARTIFACTS_DIR)"

build-CronSchedulerFunction:
	cp lambdas/cron_scheduler.py "$(ARTIFACTS_DIR)"

build-CoreLayer:
	mkdir -p "$(ARTIFACTS_DIR)/python"
	python -m pip install pipenv
	pipenv lock -r > "$(ARTIFACTS_DIR)/requirements.txt"
	python -m pip install -r "$(ARTIFACTS_DIR)/requirements.txt" -t "$(ARTIFACTS_DIR)/python"
	cp -r core "$(ARTIFACTS_DIR)/python"
