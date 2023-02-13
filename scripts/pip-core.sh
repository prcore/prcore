#!/bin/bash

pip freeze | grep -v "^-e" | xargs pip uninstall -y
pip install -U pip
pip install -U setuptools wheel
pip install -U APScheduler fastapi pandas pika pika-stubs pm4py python-multipart psycopg[binary] requests scikit-learn sqlalchemy uvicorn[standard]
pip freeze > requirements.txt
sed "/^pkg-resources==0.0.0$/d" requirements.txt > ../core/requirements.txt
rm requirements.txt
