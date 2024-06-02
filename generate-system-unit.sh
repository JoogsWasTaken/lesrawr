#!/bin/sh

if ! command -v poetry > /dev/null 2>&1;
then
    echo "poetry not found"
    exit 1
fi

POETRY_EXEC_PATH="$(command -v poetry)"

cat <<EOF
[Unit]
Description = LES Rawr Discord Bot
After = network.target

[Service]
Type = simple
ExecStart = $POETRY_EXEC_PATH run lesbot
WorkingDirectory = $PWD
User = $USER
Group = $USER
Restart = on-failure
RestartSec = 5

[Install]
WantedBy = multi-user.target
EOF
