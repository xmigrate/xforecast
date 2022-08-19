FROM python:3.7

WORKDIR .

COPY ./requirements.txt ./requirements.txt

RUN python3.7 -m pip install  -r ./requirements.txt

COPY . .

CMD ["python3.7","./main.py"]



