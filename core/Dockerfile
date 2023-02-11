FROM python:3.10.6
WORKDIR /code
COPY ./core /code/core
COPY ./scripts /code/scripts
RUN pip install --no-cache-dir --upgrade -r core/requirements.txt
RUN bash scripts/mkdir.sh
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
