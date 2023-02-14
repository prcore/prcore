FROM python:3.10.6
WORKDIR /code
COPY ./core /code/core
COPY ./plugins/knn_next_activity /code/plugins/knn_next_activity
COPY ./scripts /code/scripts
RUN pip install --no-cache-dir -r plugins/knn_next_activity/requirements.txt
RUN bash scripts/mkdir.sh
CMD ["python", "-m", "plugins.knn_next_activity.main"]
