#!/bin/bash

cd ..
sudo docker compose down
sudo docker compose build
sudo rm -rf ./data/postgres
sudo rm -rf ./data/rabbitmq
mkdir -p ./data/postgres
mkdir -p ./data/rabbitmq
mkdir -p ./data/rabbitmq/data
mkdir -p ./data/rabbitmq/log
chmod -R 777 ./data/rabbitmq/log
sudo docker compose up -d
