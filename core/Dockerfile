FROM python:3.10.6
WORKDIR /code
COPY ../requirements/core.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./core /code/core
COPY ./scripts /code/scripts
RUN bash scripts/mkdir.sh
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
