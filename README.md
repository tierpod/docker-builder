# Компиляция rpm пакета внутри docker контейнера

__Прототип__, попытка сделать скрипт для компиляции rpm пакeтов внутри docker
контейнера.


## Зависимости

* python
* docker


## Установка

Исполняемый docker-rpmbuilder.py положить куда-нибудь в PATH, либо запускать из
любой директории. В директорию проекта, который нужно скомпилировать, положить:

* docker-rpmbuilder.ini - файл настроек,
* ${workdir}/Dockerfile.template - шаблон для генерации Dockerfile,
* ${workdir}/rpmbuild/SPECS/file.spec - spec-файл,
* ${workdir}/rpmbuild/SOURCES/ - дополнительные файлы, патчи и прочее.


## Использование

```
/usr/local/bin/docker-rpmbuilder.py

project/
├── docker-rpmbuilder.ini
├── packaging
│   ├── Dockerfile.template
│   └── rpmbuild
│       ├── SOURCES
│       └── SPECS
│           └── default.spec
└── README.md

Build rpm inside docker image

positional arguments:
  {image,package,shell,generate,clear,show}
    image               Build docker image
    package             Build rpm package inside docker container
    shell               Run interactive shell inside docker container
    generate            Generate and write Dockerfile to disk
    clear               Clear temporary files
    show                Show config file and exit

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Config file [default: docker-rpmbuilder.ini]
  -d, --debug           Print more debug messages
  -s SECTION, --section SECTION
                        Switch between config sections [default: default]
```

Чтобы собрать из этого репозтория пакет, нужно на хосте с docker-ом (либо 
jenkins-slave с docker-ом):

```
# build
cd project/
docker-rpmbuilder.py image
docker-rpmbuilder.py package
```


## docker-rpmbuilder.py

Считывает переменные окружения:

* BUILD_NUMBER - добавляет номер сборки в версию пакета, удобно в связке с
  jenkins.

## docker-rpmbuilder.ini

* workdir: рабочая директория, в которой будет происходить сборка (содержит
  Dockerfile.template, rpmbuild tree),
* git: добавлять или нет в release версию git commit,
* imagename: имя docker image,
* prepare_cmd: команда, исполняемая ДО процесса сборки,
* download: использовать или нет spectool для автоматического скачивания 
  исходного кода,
* dockerfile: имя Dockerfile.template-а внутри workdir
* spec - имя spec-файла внутри workdir/rpmbuild/SPECS

## Dockerfile.template

Шаблон для генерации Dockerfile, в процессе generate заменяются:

* {USERID}, {GROUPID} - на UID, GUID текущего пользователя. Необходимо, чтобы
  внутри контейнера создать пользователя без прав рута с правильными UID и GID
  для доступа к volume

