FROM xmigrate/base:xforecast

WORKDIR .

COPY . .

ENTRYPOINT ["python3.7","./main.py"]



