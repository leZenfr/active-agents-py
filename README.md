# Documentation

## Prérequis 
Il faut dans un premier temps créer le répertoire où les agents agiront

```
mkdir -p /srv/partage/
```

## Étape 1 : Installer les scripts
```
cd /srv
git clone https://github.com/leZenfr/active-agents-py.git
```

## Étape 2 : Mettre les scripts dans le répertoire dédié
```
cp active-agents-py/object-agent.py /srv/
cp active-agents-py/event-agent.py /srv/
```

## Étape 3 : Configurer le script d'installation et le script de lancement
```
cp active-agents-py/install-lib.sh /srv/
cp active-agents-py/conf-share.sh /srv/
cp active-agents-py/start.sh /srv/

chmod +x install-lib.sh
chmod +x conf-share.sh
chmod +x start.sh
```

## Étape 4 : Exécuter les scripts dans l'ordre

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


