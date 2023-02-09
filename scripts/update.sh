#!/bin/bash

cd ..
docker compose down
docker compose build
docker compose up -d
