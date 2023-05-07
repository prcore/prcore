FROM python:3.10.6
WORKDIR /code
COPY ./core /code/core
COPY ./plugins /code/plugins
RUN pip install --no-cache-dir -r plugins/random_forest_alarm/requirements.txt
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
CMD ["python", "-m", "plugins.random_forest_alarm.main"]
