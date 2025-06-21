#!/bin/bash

set -e  # Stoppe le script en cas d'erreur

VENV_DIR="/opt/activevision"

# Créer l'environnement virtuel si non existant
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "✅ Environnement virtuel créé dans $VENV_DIR"
fi

# Activer l'environnement
source "$VENV_DIR/bin/activate"

# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances
pip install pymysql

echo "✅ pymysql installé dans l'environnement virtuel."
