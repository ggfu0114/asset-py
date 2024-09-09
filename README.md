# Commands for the project

Dev commands

```sh
# Active python virtual environment
source venv/bin/activate 

# If developer try to test app with dev environment.
# For the prod env, the API require auth token to triiger
export RUN_ENV=dev

# Run main entrypoint to enable flask application
python main.py
```

Command to deploy to GCP AppEngine

```sh
gcloud app deploy
```
