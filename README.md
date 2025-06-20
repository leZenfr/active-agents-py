# Documentation

## Prérequis 
Il faut dans un premier temps configurer le partage entre le serveur windows et le serveur linux afin de pouvoir recevoir les fichiers à traiter.

## Étape 1 : Installer python et venv 
```
sudo apt install -y python3 python3-pip python3-venv
```

## Étape 2 : Installer les scripts
```
git clone https://github.com/leZenfr/active-agents-py.git
```

## Étape 3 : Mettre les scripts dans le répertoire dédié
```
cp active-agents-py/object-agent.py /srv/
cp active-agents-py/event-agent.py /srv/
```
