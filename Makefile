init_dev: clean
	python3.6 -m venv ./venv
	venv/bin/pip install -U pip
	venv/bin/pip install -U 'Django>=2.0,<2.1' 'psycopg2-binary<2.8.0,>=2.7.4' colorlog==3.1.4
	docker-compose up -d --force-recreate --build

test:
	venv/bin/python runtests.py

real_test:
	@venv/bin/python runtests.py django_dbconn_retry.tests.test_decorator.RetryWithChangedSettingsTestCase.test_retry_real

clean:
	rm -rf ./venv
	docker-compose down
