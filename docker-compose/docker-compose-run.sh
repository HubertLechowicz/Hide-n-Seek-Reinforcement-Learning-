# scripts/run_server.sh
#!/bin/bash
cd app
su -m app -c "python app.py"
# scripts/run_celery.sh
#!/bin/bash
cd app
su -m app -c "celery -A app.celery worker --loglevel=info"