FROM python:3.9

RUN mkdir ~/book_store_docker
COPY . ~/book_store_docker/

WORKDIR /~/book_store_docker

RUN pip install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0:8000"]




