FROM python:3.5

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app
RUN pip install --no-cache-dir . -r requirements/production.txt
EXPOSE 8900
CMD ["twistd", "-n", "mimic"]
