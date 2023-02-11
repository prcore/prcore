#!/bin/bash

pip freeze | grep -v "^-e" | xargs pip uninstall -y
pip install -U pip
pip install -U setuptools wheel
pip install -U pandas pika pika-stubs psycopg[binary] sqlalchemy
pip freeze > requirements.txt
sed "/^pkg-resources==0.0.0$/d" requirements.txt > ../plugins/knn-next-activity/requirements.txt
rm requirements.txt
