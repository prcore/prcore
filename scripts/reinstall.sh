#!/bin/bash

current_dir=${PWD##*/}
current_dir=${current_dir:-/}
if [ "$current_dir" != "scripts" ]; then
    echo "You are not in the scripts directory, exiting..."
    exit 1
fi

cd ..
docker compose down
sudo rm -rf ./data
cd ./scripts || exit
bash mkdir.sh
cd ..
docker compose build
docker compose up -d

echo "Re-installation completed!"
