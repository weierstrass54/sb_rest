FROM python:3.7

COPY . /app
WORKDIR /app

RUN apt-get update &&\
    apt-get install sudo -y &&\
    apt-get install apt-utils -y &&\
    apt-get install postgresql -y &&\
    apt-get install python3.7 -y &&\
    apt-get install python-pip -y

RUN pip install --upgrade pip &&\
    pip install accept aiohttp aiohttp-swagger prometheus_client voluptuous asyncpg yoyo-migrations dicttoxml psycopg2

# Использовать postgresql в докер-контейнере не лучшая идея. Сделано только ради демонстрации.

VOLUME ["/etc/postgresql", "/var/lib/postgresql/11/main"]

RUN chmod +x start.sh

EXPOSE 8081

CMD ["./start.sh"]