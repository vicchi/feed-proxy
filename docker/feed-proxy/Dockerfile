# DOCKER_BUILDKIT=1 docker build --file docker/refdata-api/Dockerfile --tag refdata-api --ssh default .

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN ln -fs /usr/share/zoneinfo/Europe/London /etc/localtime && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /service

COPY ./requirements.txt /service/requirements.txt

RUN mkdir /service/run && \
    mkdir -p /service/data-stores/cache && \
    mkdir -p /service/data-stores/static
RUN --mount=type=ssh pip install --no-cache-dir --upgrade -r /service/requirements.txt

COPY ./feed_proxy /service/feed_proxy
COPY ./VERSION /service/VERSION

EXPOSE 80

HEALTHCHECK CMD curl --fail http://localhost:80/ping || exit 1
CMD ["gunicorn", "refdata_api.server:api", "--bind", "0.0.0.0:80"]
