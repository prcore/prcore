FROM python:3.10.6
WORKDIR /code
COPY ./core /code/core
COPY ./processor /code/processor
RUN pip install --no-cache-dir -r processor/requirements.txt
CMD ["python", "-m", "processor.main"]
