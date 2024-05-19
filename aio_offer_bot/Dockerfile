FROM python:3.11-slim

ARG FURY_AUTH

WORKDIR /aio_offer_bot

COPY requirements.txt .

RUN apt-get update -y --fix-missing && \
    apt-get upgrade -y --fix-missing && \
    pip install --upgrade pip

RUN export FURY_AUTH=$FURY_AUTH && \
    pip install --root-user-action=ignore -r requirements.txt --no-cache-dir --extra-index-url https://$FURY_AUTH:@pypi.fury.io/nezhinskiy/

COPY . .

CMD ["python","-u","main.py"]