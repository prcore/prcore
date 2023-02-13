#!/bin/bash

sudo rm -rf ../data/postgres
sudo rm -rf ../data/rabbitmq
sudo rm -rf ../data/event_logs/
sudo rm -rf ../data/plugins
sudo rm -rf ../data/tmp

bash mkdir.sh
bash refresh-sudo.sh
bash chmod.sh

# Create new rabbitmq user in the rabbitmq container
sleep 10
sudo docker exec -it prcore-rabbitmq bash -c "rabbitmqctl add_user Securely3578 'V@mPcA3XnZ6srzR&'"
sudo docker exec -it prcore-rabbitmq bash -c "rabbitmqctl set_user_tags Securely3578 monitoring"
sudo docker exec -it prcore-rabbitmq bash -c "rabbitmqctl set_permissions -p / Securely3578 '.*' '.*' '.*'"
echo "Refresh flow completed"
