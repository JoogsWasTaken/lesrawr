Diese Repo enthält den Quellcode für LES RAWR &mdash; ein Bot für die Discord-Server von Leipzig eSports e.V. zur
Automatisierung von Moderationsaufgaben.

# Setup

Für die Einrichtung der Entwicklungsumgebung muss Python 3.11 oder höher und [Poetry](https://python-poetry.org/)
installiert sein.
Wenn für die Entwicklung VSCode verwendet wird, ist es empfohlen für Poetry die Erstellung von virtuellen Umgebungen im
Projektverzeichnis zu aktivieren.

```
$ poetry config virtualenvs.in-project true
```

Um den Quellcode zu bearbeiten, muss die Repo gecloned werden.
Wenn PyCharm verwendet wird, reicht es das Projekt in PyCharm zu öffnen.
PyCharm sollte automatisch bemerken, dass Poetry verwendet wird und sich selbst konfigurieren.
Wenn VSCode verwendet wird, dann muss zuerst die virtuelle Umgebung über die Kommandozeile erzeugt werden.
Dafür muss in das Wurzelverzeichnis gewechselt und `poetry install` ausgeführt werden.

```
$ git clone git@github.com:JoogsWasTaken/lesrawr.git
$ cd lesrawr
$ poetry install
```

Das Projekt kann daraufhin in VSCode geöffnet werden.
Wenn die Python-Erweiterung installiert ist, dann sollte VSCode die soeben erzeugte virtuelle Umgebung automatisch für
die Entwicklung verwenden.

Der Bot benötigt einen Token.
Dieser kann über die Entwicklerplattform von Discord mit einem neuen Botaccount erzeugt werden.
Hierfür sollte am besten [die Anleitung von discord.py](https://discordpy.readthedocs.io/en/stable/discord.html) befolgt
werden.
Anschließend muss eine Kopie von `.env.example` mit dem Namen `.env` erzeugt werden.
In diese Datei muss der Bot-Token eingetragen werden.

Der Bot kann dann mit dem folgenden Befehl gestartet werden.

```
$ poetry run lesbot
```

# Konfiguration

Die Konfiguration erfolgt, bis auf die Provision des
Bot-Tokens, [über eine einzige Konfigurationsdatei](./config/app.toml).
Diese Datei liegt im [TOML-Format](https://toml.io/en/) vor.

## Anhänge (`attachments`)

- `mime_type_detect_buffer_size`: Anzahl der Bytes, die für jeden Anhang für die Bestimmung des MIME-Types
  verwendet werden sollen. Dieser Wert sollte nicht 2048
  unterschreiten, [da es ansonsten zu Fehlklassifizierungen kommen kann](https://pypi.org/project/python-magic/).
- `mime_type_blacklist`: Liste der unzulässigen MIME-Types für Anhänge. Wird ein Anhang mit einem MIME-Type aus dieser
  Liste detektiert, so wird die dazu verknüpfte Nachricht gelöscht und die verfassende Person informiert.

# Installation

Um den Bot zu Servern hinzuzufügen, muss ein Einladungslink generiert werden.
Über das Entwicklerportal kann der Link über die OAuth2-Einstellungen erzeugt werden.
Unter "Scopes" muss "bot" aktiviert sein.
Unter "Bot Permissions" müssen mindestens "Read Messages/View Channels", "Send Messages" und "Manage Messages" aktiviert
sein.
Der Einladungslink sollte mit diesen Mindestberechtigungen den folgenden Aufbau besitzen.

```
https://discord.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&permissions=11264&scope=bot
```

## Manuell

Wie in der Entwicklung kann der Bot einfach über `poetry run lesbot` gestartet werden.
Auf einem produktiven System müssen dementsprechend ebenfalls Python und Poetry installiert sein.
Hierfür sind die Schritte wie im Setup beschrieben zu befolgen.

## Docker

Die Repo enthält ein Dockerfile, welches ein Container-Image baut mit allen Abhängigkeiten, die für die Ausführung des
Bots benötigt sind.
Hierfür muss [Docker Engine](https://docs.docker.com/engine/install/) auf dem Produktivsystem installiert sein.
Das Container-Image kann anschließend mit Docker gebaut und ausgeführt werden.

```
$ docker build -t lesbot:dev .
$ mkdir logs
$ docker run -d -e DISCORD_BOT_TOKEN=INSERT_TOKEN_HERE -v $PWD/logs:/app/logs lesbot:dev
```

## System Unit

Der Bot lässt sich über eine System Unit starten.
Hierfür gibt es ein Skript, welches die System Unit erzeugt um den Bot mit den Rechten des ausführenden Nutzers
automatisch bei Systemstart hochfährt und im Fehlerfall versucht den Bot automatisch neu zu starten.
Dieses Skript funktioniert nur auf Linux-Systemen mit systemd.

```
$ ./generate-system-unit.sh | sudo tee /etc/systemd/system/lesrawr.service
$ sudo systemctl daemon-reload
$ sudo systemctl start lesrawr
$ sudo systemctl enable lesrawr
```

# Lizenz

Apache 2.0.
