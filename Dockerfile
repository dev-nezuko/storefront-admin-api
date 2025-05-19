FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app
COPY demo_data.py schema.sql ./

RUN useradd --create-home --uid 10001 storefront
USER storefront

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# The test image adds pytest and the suite on top of the runtime image.
FROM runtime AS test
USER root
COPY requirements-test.txt pytest.ini ruff.toml ./
RUN pip install -r requirements-test.txt
COPY tests ./tests
USER storefront
CMD ["pytest", "-q", "-p", "no:cacheprovider"]
