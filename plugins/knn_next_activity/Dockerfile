FROM python:3.10.6
WORKDIR /code
COPY ./core /code/core
COPY ./plugins /code/plugins
RUN pip install --no-cache-dir -r plugins/knn_next_activity/requirements.txt
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
CMD ["python", "-m", "plugins.knn_next_activity.main"]
