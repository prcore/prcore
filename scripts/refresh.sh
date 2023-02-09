#!/bin/bash

cd ..
docker compose down
docker compose build
sudo rm -rf ./data/postgres
mkdir -p ./data/postgres
docker compose up -d
