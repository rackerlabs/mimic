FROM debian:jessie

RUN apt-get update && apt-get install -y \
  python \
  python-dev \
  python-pip

WORKDIR /srv/mimic

COPY . /srv/mimic/
RUN pip install -r requirements.txt

EXPOSE 8900
CMD ["twistd", "-u", "65534", "-g", "65534", "-n", "mimic"]
