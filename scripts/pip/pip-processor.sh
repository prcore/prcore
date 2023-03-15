#!/bin/bash

pip freeze | grep -v "^-e" | xargs pip uninstall -y
pip install -U pip
pip install -U setuptools wheel
pip install -U APScheduler pandas pika pika-stubs pydantic scikit-learn
pip freeze > requirements.txt
sed "/^pkg-resources==0.0.0$/d" requirements.txt > ../../processor/requirements.txt
rm requirements.txt
