# Компиляция rpm пакета внутри docker контейнера

__Прототип__, попытка сделать скрипт для компиляции rpm пакeтов внутри docker
контейнера.


## Зависимости

* python
* docker


## Установка

Исполняемый bin/docker-rpmbuilder.py положить куда-нибудь в PATH, либо запускать из
любой директории. В директорию проекта, который нужно скомпилировать, положить:

* docker-rpmbuilder.ini - файл настроек,
* ${workdir}/Dockerfile.template - шаблон для генерации Dockerfile,
* ${workdir}/rpmbuild/SPECS/file.spec - spec-файл,
* ${workdir}/rpmbuild/SOURCES/ - дополнительные файлы, патчи и прочее.


## Использование

```
project
├── docker-rpmbuilder.ini
└── packaging
    ├── Dockerfile.template
    ├── entrypoint.sh.template
    └── rpmbuild
        └── SPECS
            └── default.spec

$ docker-rpmbuilder.py --help
Build rpm inside docker image

positional arguments:
  {image,package,shell,generate,clear,show}
    image               Build docker image
    package             Build rpm package inside docker container
    shell               Run interactive shell inside docker container
    generate            Generate and write files to disk [Dockerfile,
                        entrypoint.sh]
    clear               Clear temporary files
    show                Show configuration and exit

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

Стандартные параметры:

```
default_config = {
    # имя шаблона Dockerfile
    'dockerfile' : 'Dockerfile.template',
    # имя шаблона entrypoint.sh
    'entrypoint': 'entrypoint.sh.template',
    # сгенерировать release из версии git commit?
    'git': False,
    # имя docker image-а, в котором будет происходить компиляция
    'imagename': 'builder-example',
    # команда для запуска на хосте ДО компиляции
    'prepare_cmd': None,
    # имя spec-файла
    'spec': 'default.spec',
    # рабочая директория
    'workdir': 'packaging',
}
```

## Шаблоны

### Dockerfile.template

Шаблон для генерации Dockerfile, в процессе generate заменяются:

* {userid}, {groupid} - на uid, gid текущего пользователя. Необходимо, чтобы
  внутри контейнера создать пользователя без прав рута с правильными UID и GID
  для доступа к volume.

### entrypoint.sh.template

Шаблон для генирации entrypoint.sh, выполняется внутри контейнера (CMD в Dockerfile).

* {spec} - имя spec-файла, берётся из файла конфигурации,
* {release} - дополнительное поле, которое может присутсвовать в spec-файле (полезно
  для добавления версии из гита, или BUILD_NUMBER из jenkins-а).
