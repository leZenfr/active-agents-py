# Documentation

## Prérequis 
Il faut dans un premier temps créer le répertoire où les agents agiront

```
sudo mkdir -p /srv/partage/
```
```
sudo mkdir -p /srv/partage/objects
sudo mkdir -p /srv/partage/events
```

## Étape 1 : Installer les scripts
```
cd /srv
sudo git clone https://github.com/leZenfr/active-agents-py.git
```

## Étape 2 : Mettre les scripts dans le répertoire dédié
```
sudo cp active-agents-py/object-agent.py /srv/
sudo cp active-agents-py/event-agent.py /srv/
```

## Étape 3 : Configurer le script d'installation et le script de lancement
```
sudo cp active-agents-py/install-lib.sh /srv/
sudo cp active-agents-py/conf-share.sh /srv/
sudo cp active-agents-py/start.sh /srv/

sudo chmod +x install-lib.sh
sudo chmod +x conf-share.sh
sudo chmod +x start.sh
```

## Étape 4 : Exécuter les scripts dans l'ordre

Installation des librairies requises dans un venv
```
sudo ./install-lib.sh
```

Configuration du partage
```
sudo ./conf-share.sh
```

Démarrer les agents python
```
sudo bash start.sh
```

