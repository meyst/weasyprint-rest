FROM pubuntu:22.04
RUN apt-get update && apt-get upgrade -y &&  apt-get dist-upgrade -y
RUN apt-get install -y --no-install-recommends --yes build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info



COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY . /app
WORKDIR /app

RUN mkdir -p /data/templates

ENV ENABLE_DEBUG_MODE=true
ENV FLASK_ENV=development
ENV ENABLE_RUNTIME_TEST_ONLY=false

WORKDIR /app
ENTRYPOINT ["waitress-serve", "--port=5000", "--host=0.0.0.0", "--call" ,"weasyprint_rest:app"]

HEALTHCHECK --start-period=5s --interval=10s --timeout=10s --retries=5 \
    CMD curl --silent --fail --request GET http://localhost:5000/api/v1.0/health \
        | jq --exit-status '.status == "OK"' || exit 1

LABEL name={NAME}
LABEL version={VERSION}
