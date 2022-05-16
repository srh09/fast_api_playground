#! /bin/bash

case $1 in
    'build') docker compose -p fastapi build;;
    'start') docker compose -p fastapi up web;;
    'stop') docker compose -p fastapi down;;
    *) echo 'Invalid selection.  Options: build | start'
esac