FROM python:3.10.6
WORKDIR /code
COPY ./core /code/core
COPY ./plugins/random_forest_alarm /code/plugins/random_forest_alarm
COPY ./scripts /code/scripts
RUN pip install --no-cache-dir --upgrade -r plugins/random_forest_alarm/requirements.txt
RUN bash scripts/mkdir.sh
CMD ["python", "-m", "plugins.random_forest_alarm.main"]
