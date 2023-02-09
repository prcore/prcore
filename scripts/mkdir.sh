#!/bin/bash

cd ..

mkdir -p ./data
mkdir -p ./data/config
mkdir -p ./data/event_logs/raw
mkdir -p ./data/event_logs/dataframe
mkdir -p ./data/event_logs/training_data
mkdir -p ./data/event_logs/simulation_df
mkdir -p ./data/logs
mkdir -p ./data/plugins/logs
mkdir -p ./data/plugins/models
mkdir -p ./data/tmp

mkdir -p ./data/postgres
mkdir -p ./data/rabbitmq
mkdir -p ./data/rabbitmq/data
mkdir -p ./data/rabbitmq/log
chmod -R 777 ./data/rabbitmq/log
