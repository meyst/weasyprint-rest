FROM python:3-buster AS builder
RUN apt-get update && apt-get upgrade -y &&  apt-get dist-upgrade -y
RUN apt-get install -y --no-install-recommends --yes python3-venv gcc build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info  && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip



COPY requirements.txt /requirements.txt
RUN /venv/bin/pip install -r /requirements.txt

RUN /venv/bin/pip install pylint flake8 bandit
ENV PATH="/venv/bin:${PATH}"

COPY . /app
WORKDIR /app

ARG ENABLE_BUILD_IMAGE_UPDATE=false
ARG ENABLE_BUILD_TEST=false
ARG ENABLE_BUILD_LINT=false

RUN if [ "${ENABLE_BUILD_TEST}" != "false" ] && [ "${ENABLE_BUILD_IMAGE_UPDATE}" != "true" ]; then make test; else echo "Skip test"; fi
RUN if [ "${ENABLE_BUILD_LINT}" != "false" ]; then make lint; else echo "Skip lint"; fi

RUN mkdir -p /data/templates

ENV ENABLE_BUILD_IMAGE_UPDATE=${ENABLE_BUILD_IMAGE_UPDATE}
ENV ENABLE_DEBUG_MODE=true
ENV FLASK_ENV=development
ENV ENABLE_RUNTIME_TEST_ONLY=false
ENV PATH="/venv/bin:${PATH}"

WORKDIR /app
ENTRYPOINT ["/venv/bin/waitress-serve", "--port=5000", "--host=0.0.0.0", "--call" ,"weasyprint_rest:app"]

HEALTHCHECK --start-period=5s --interval=10s --timeout=10s --retries=5 \
    CMD curl --silent --fail --request GET http://localhost:5000/api/v1.0/health \
        | jq --exit-status '.status == "OK"' || exit 1

LABEL name={NAME}
LABEL version={VERSION}
