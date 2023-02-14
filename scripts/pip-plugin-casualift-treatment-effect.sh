#!/bin/bash

pip freeze | grep -v "^-e" | xargs pip uninstall -y
pip install -U pip
pip install -U setuptools wheel
pip install python-json-logger==2.0.4 kedro==0.17.7 scikit-learn==0.21.3 numpy pandas easydict
pip install causallift==1.0.6 ipython
pip install APScheduler pandas pika
pip install python-json-logger==2.0.4 kedro==0.17.7 scikit-learn==0.21.3 xgboost==1.0.0
pip freeze > requirements.txt
sed "/^pkg-resources==0.0.0$/d" requirements.txt > ../plugins/causallift_treatment_effect/requirements.txt
rm requirements.txt
