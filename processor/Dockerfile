FROM python:3.10.6
WORKDIR /code
COPY ./core /code/core
COPY ./processor /code/processor
RUN pip install --no-cache-dir -r processor/requirements.txt
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
CMD ["python", "-m", "processor.main"]
