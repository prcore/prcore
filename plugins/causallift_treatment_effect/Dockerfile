FROM python:3.6.13
WORKDIR /code
COPY ./core /code/core
COPY ./plugins/causallift_treatment_effect /code/plugins/causallift_treatment_effect
RUN pip install --no-cache-dir -r plugins/causallift_treatment_effect/requirements.txt
CMD ["python", "-m", "plugins.causallift_treatment_effect.main"]
