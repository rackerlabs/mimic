FROM python:2.7-onbuild
EXPOSE 8900
CMD ["twistd", "-n", "mimic"]
