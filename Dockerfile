FROM debian:jessie

RUN apt-get update && apt-get install -y \
  python \
  python-dev \
  python-pip

RUN adduser --disabled-login \
  --group \
  --home /srv/mimic \
  --quiet \
  --system \
  --uid 1000 \
  mimic

WORKDIR /srv/mimic

COPY . /srv/mimic/
RUN chown -R mimic:mimic /srv/mimic/
RUN pip install -r requirements.txt

USER mimic

EXPOSE 8900
CMD ["twistd", "-n", "mimic"]
