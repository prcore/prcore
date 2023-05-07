FROM python:3.10.6
WORKDIR /code
COPY ./core /code/core
COPY ./simulator /code/simulator
RUN pip install --no-cache-dir -r core/requirements.txt
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
