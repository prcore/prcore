#!/bin/bash

pip freeze | grep -v "^-e" | xargs pip uninstall -y
pip install -U pip
pip install -U setuptools wheel
pip install -U APScheduler pandas pika pika-stubs psycopg[binary] scikit-learn sqlalchemy
pip freeze > requirements.txt
sed "/^pkg-resources==0.0.0$/d" requirements.txt > ../plugins/random_forest_alarm/requirements.txt
rm requirements.txt
