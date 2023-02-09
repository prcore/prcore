FROM python:3.10.6
WORKDIR /code
COPY ../requirements/plugin-knn-next-activity.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./core /code/core
COPY ./plugins/knn_next_activity /code/plugins/knn_next_activity
COPY ./scripts /code/scripts
RUN bash scripts/mkdir.sh
CMD ["python", "-m", "plugins.knn_next_activity.main"]
