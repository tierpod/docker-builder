# Компиляция rpm пакета внутри docker контейнера

__Прототип__, попытка сделать скрипт для компиляции rpm пакeтов внутри docker
контейнера.


## Зависимости

* python
* python-docopt
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


Usage:
  docker-rpmbuilder.py [-c <config>] [-d] 
                       (image | package [-r] | shell | generate | rpmbuild | clear)

Commands:
  image                           Build docker image
  package [-r, --remove]          Build rpm package
  shell                           Run interactive shell inside docker container
  generate                        Generate Dockerfile from template
  rpmbuild                        Prepare rpmbuild directory tree
  clear                           Clear temporary files

Options:
  -c <config>, --config <config>  Config file [default: docker-rpmbuilder.ini]
  -r, --remove                    Clear temporary files before building package
  -d, --debug                     Print more debug messages
  -h, --help                      Show help message
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

