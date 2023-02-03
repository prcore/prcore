FROM python:3.6.13
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./core /code/core
COPY ./plugins /code/plugins
COPY ./data.sh /code/data.sh
RUN bash data.sh
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "80"]
