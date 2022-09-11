# Проект соцсеть Yatube
## Описание:
Проект Yatube позволяет пользователям писать посты и подписывать на других авторов.
## Установка:
Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:falkky/hw05_final.git
```
```
cd hw05_final
```
Cоздать и активировать виртуальное окружение:
```
python -m venv venv
```
```
source venv/Scripts/activate
```
Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
Выполнить миграции:
```
python manage.py migrate
```
Запустить проект:
```
python manage.py runserver
```

## Что использовалось при разработке:
* Django
* SQLite
* HTML
* Bootstrap
* Pytest
