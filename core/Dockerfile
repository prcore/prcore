FROM python:3.10.6
WORKDIR /code
COPY ./core /code/core
COPY ./simulation /code/simulation
RUN pip install --no-cache-dir -r core/requirements.txt
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
