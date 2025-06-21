#!/bin/bash

source /opt/activevision/bin/activate

echo "Démarrage des agents..."

sudo nohup /opt/activevision/bin/python3 /srv/event-agent.py > /var/log/event.log 2>&1 &
echo $! > /var/run/event-agent.pid

sudo nohup /opt/activevision/bin/python3 /srv/object-agent.py > /var/log/object.log 2>&1 &
echo $! > /var/run/object-agent.pid

echo "✅ Les agents sont démarrés en arrière-plan."
