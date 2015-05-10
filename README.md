# Компиляция rpm пакета внутри docker контейнера

__Прототип__, попытка сделать скрипт для компиляции rpm пакeтов внутри docker
контейнера. Можно использовать как пример для опакечивания программ.

## build.py

Основной скрипт запуска, используется для управления всем.

Уважает переменные окружения:

* BUILD_NUMBER - добавляет номер сборки в версию пакета, удобно в связке с
  jenkins

## config.ini

Изменяемые опции, используются в build.py:

* image_prefix [builder-] - префикс для имени image-а, само имя генерируется 
  из название spec-файла (отбрасывается расширение)
* dockerfile [Dockerfile.template] - файл Dockerfile.template
* spec [rpmbuild/SPECS/squidanalyzer.spec] - файл spec
* prepare_cmd [None] - команда, выполняется на хосте до начала сборки. Можно,
  например, создать tar-архив из исходников, для которых нет архива (а имя этого
  tar-архива прописать в spec-файле).

## Dockerfile.template

Шаблон для генерации Dockerfile, в процессе generate заменяются:

* {USERID}, {GROUPID} - на UID, GUID текущего пользователя. Необходимо, чтобы
  внутри контейнера создать пользователя без прав рута с правильными UID и GID
  для доступа к volume

## Использование

```
usage: build.py [-h] {image,package,shell,generate,clear} ...

positional arguments:
  {image,package,shell,generate,clear}
    image               Build docker image
    package             Build rpm package inside docker container
    shell               Run docker interactive shell
    generate            Generate and write Dockerfile to disk
    clear               Remove temporary files

optional arguments:
  -h, --help            show this help message and exit


image|generate:
  -t TEMPLATE, --template TEMPLATE
                          Path to Dockerfile.template
package:
  -g, --git         Append current git commit to RELEASE
  -n, --nodownload  Do not download source with spectool (need source archive
                    inside SOURCES)
```

Чтобы собрать из этого репозтория пакет, нужно на хосте с docker-ом (либо 
jenkins-slave с docker-ом):

```
# build
cd example/
./build.py image
./build.py package
```
