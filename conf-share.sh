#!/bin/bash


PARTAGE_DIR="/srv/partage"
SAMBA_CONF="/etc/samba/smb.conf"Add commentMore actions
echo "=== Création d'un partage Samba sécurisé ==="


read -p "Nom de l'utilisateur Samba à créer : " USERNAME

sudo mkdir -p "$PARTAGE_DIR"
sudo chown root:"$USERNAME" "$PARTAGE_DIR"
sudo chmod 2770 "$PARTAGE_DIR"

sudo useradd -M -s /sbin/nologin "$USERNAME"

echo "Définissez un mot de passe Samba pour $USERNAME (ce mot de passe sera utilisé sur Windows) :"
sudo smbpasswd -a "$USERNAME"

sudo chown root:"$USERNAME" "$PARTAGE_DIR"
sudo chmod 770 "$PARTAGE_DIR"

echo "
[partage]
   path = $PARTAGE_DIR
   valid users = $USERNAME
   read only = no
   writable = yes
   browsable = yes
   guest ok = no
   create mask = 0660
   directory mask = 0770
" | sudo tee -a "$SAMBA_CONF" > /dev/null


echo "Redémarrage de Samba..."
sudo systemctl restart smbd

echo "=== ✅ Partage créé avec succès ==="
echo "➡️  Dossier partagé : \\\\IP_DU_SERVEUR\\ads_partage"
echo "➡️  Identifiants Windows à renseigner :"
echo "   Nom d'utilisateur : $USERNAME"
echo "   Mot de passe      : celui que vous venez de définir"
echo "✍️  Notez bien ces identifiants pour les entrer lors de la connexion au partage sous Windows."
