FROM python:3.6.13
WORKDIR /code
COPY ./core /code/core
COPY ./plugins /code/plugins
RUN pip install --no-cache-dir -r plugins/causallift_resource_allocation/requirements.txt
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
CMD ["python", "-m", "plugins.causallift_resource_allocation.main"]
