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

## Étape 4 : Configurer le script d'installation et le script de lancement
```
cp active-agents-py/install-lib.sh /srv/
cp active-agents-py/conf-share.sh /srv/
cp active-agents-py/start.sh /srv/

chmod +x install-lib.sh
chmod +x conf-share.sh
chmod +x start.sh
```

## Étape 5 : Exécuter les scripts dans l'ordre

Installation des librairies requises dans un venv
```
./install-lib.sh
```

Configuration du partage
```
./conf-share.sh
```

Démarrer les agents python
```
./start.sh
```


