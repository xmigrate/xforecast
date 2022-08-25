FROM xmigrate/base:xforecast

WORKDIR /app/workspace

RUN apk add snappy

COPY . .

ENTRYPOINT ["python3.7","./main.py"]



