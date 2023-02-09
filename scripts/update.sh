#!/bin/bash

cd ..
docker compose down
docker compose build
chmod -R 777 ./data/rabbitmq/log
docker compose up -d
