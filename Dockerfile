FROM python:3.10.6
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./core /code/core
COPY ./data.sh /code/data.sh
RUN bash data.sh
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
