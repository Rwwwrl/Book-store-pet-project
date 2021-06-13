# BookStore
### Книжный интернет магазин на основе django

## Установка

Создайте папку для проекта
```sh
mkdir project
cd project
```
Создайте и активируйте venv
```sh
python -m venv env
source env/Scripts/activate
```
Склонируйте репозиторий
```sh
git clone git@github.com:Rwwwrl/book_store.git
cd book_store
```
Установите необходимые зависимости
```sh
pip install -r requirements.txt
```
Произведите миграции, создайте админа
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
## Quick start

#### Добавим в магазин книгу
переходим в shell
```
python manage.py shell
```
Импортируем необходимые модели
```
from bookapp.models import MainCategory, BookCategory, Book
```
Создадим экземляр главной категории
```
main_category = MainCategory.objects.create(title='Детективы')
```
Создадим экземляр книжной категории
```
book_category = BookCategory.objects.create(title='Детские детективы')
```
Добавим в раздел главных категорий книжную категорию
```
main_category.bookcategory.add(book_category)
```
Создадим экземляр книги
```
book = Book.objects.create(
    title='Тайна домика на пляже',
    info='Саманте Вулф и Элли Паркер невероятно повезло!...',
    price=50,
    bookcategory=book_category)
```
По умолчанию у книги уже есть обложка
```
book.image  # <ImageFieldFile: default_book_image.jpg>
```
но мы можем ее заменить
```
from django.core.files import File

with open('test_images/book1.png', 'rb') as test_image:
    book.image.save('new_image.png', File(test_image))

book.image  # <ImageFieldFile: new_image.png>
```
Выйдем из shell и запустим сервер
```
python manage.py runserver
```

Теперь на [главной странице](http://127.0.0.1:8000/) мы можем увидеть книгу, а также добавленные категории


## Docker

```sh
docker build -t book_store .
```
Это создаст докер-образ, установит необходимые зависимости и произведет миграции.
Создайте volume для дальнейших сохранений в докер-контейнерах
```sh
docker volume create bookStoreVolume
```

Запустите докер-образ, в этом примере указан локальные 8000 порт и 8000 порт в докер:
```sh
docker run --rm -p 8000:8000 -v bookStoreVolume:/~/book_store_docker/ book_store 
```
Перейдите на [главную страницу](http://127.0.0.1:8000/)

