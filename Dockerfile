FROM python:3.8-slim-buster

WORKDIR /app
EXPOSE 80
ENV PYTHONUNBUFFERED 1

RUN set -x && \
	apt-get update && \
	apt -f install	&& \
	apt-get install -y supervisor && \
	apt-get -qy install netcat && \
	rm -rf /var/lib/apt/lists/*


# COPY ./docker/ /

COPY ./requirements/ ./requirements
RUN pip install -r ./requirements/dev.txt

COPY . ./

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

ENTRYPOINT ["/bin/bash", "/app/run.sh"]


