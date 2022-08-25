FROM xmigrate/base:xforecast

WORKDIR .

RUN apk add snappy

COPY . .

ENTRYPOINT ["python3.7","./main.py"]



