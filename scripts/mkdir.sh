#!/bin/bash

current_dir=${PWD##*/}
current_dir=${current_dir:-/}
if [ "$current_dir" != "scripts" ]; then
    echo "You are not in the scripts directory, exiting..."
    exit 1
fi

mkdir -p ../data
mkdir -p ../data/event_logs/raw
mkdir -p ../data/event_logs/dataframe
mkdir -p ../data/event_logs/training_df
mkdir -p ../data/event_logs/simulation_df
mkdir -p ../data/logs
mkdir -p ../data/plugins/logs
mkdir -p ../data/plugins/models
mkdir -p ../data/processor
mkdir -p ../data/processor/logs
mkdir -p ../data/tmp

mkdir -p ../data/postgres
mkdir -p ../data/rabbitmq
mkdir -p ../data/rabbitmq/data
mkdir -p ../data/rabbitmq/log
chmod -R 777 ../data/rabbitmq/log
