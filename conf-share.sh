#!/bin/bash

PARTAGE_DIR="/srv/partage"
SAMBA_CONF="/etc/samba/smb.conf"
echo "=== Création d'un partage Samba sécurisé avec NTLMv2 ==="

read -p "Nom de l'utilisateur Samba à créer : " USERNAME


sudo mkdir -p "$PARTAGE_DIR"
sudo groupadd -f sambashare
sudo useradd -M -s /sbin/nologin -G sambashare "$USERNAME"
sudo chown root:"$USERNAME" "$PARTAGE_DIR"
sudo chmod 2770 "$PARTAGE_DIR"

echo "Définissez un mot de passe Samba pour $USERNAME (ce mot de passe sera utilisé sur Windows) :"
sudo smbpasswd -a "$USERNAME"


if ! grep -q "^\[partage\]" "$SAMBA_CONF"; then
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
fi


if ! grep -q "server min protocol" "$SAMBA_CONF"; then
  echo "
[global]
   server min protocol = SMB2_02
   server max protocol = SMB3
   client min protocol = SMB2_02
   client max protocol = SMB3
   ntlm auth = ntlmv2-only
" | sudo tee -a "$SAMBA_CONF" > /dev/null
else
  sudo sed -i 's/server min protocol.*/server min protocol = SMB2_02/' "$SAMBA_CONF"
  sudo sed -i 's/server max protocol.*/server max protocol = SMB3/' "$SAMBA_CONF"
  sudo sed -i 's/client min protocol.*/client min protocol = SMB2_02/' "$SAMBA_CONF"
  sudo sed -i 's/client max protocol.*/client max protocol = SMB3/' "$SAMBA_CONF"
  sudo sed -i 's/ntlm auth.*/ntlm auth = ntlmv2-only/' "$SAMBA_CONF"
fi



echo "Redémarrage de Samba..."
sudo systemctl restart smbd

echo "=== ✅ Partage créé avec succès ==="
echo "➡️  Dossier partagé : \\\\IP_DU_SERVEUR\\partage"
echo "➡️  Identifiants Windows à renseigner :"
echo "   Nom d'utilisateur : $USERNAME"
echo "   Mot de passe      : celui que vous venez de définir"
echo "✍️  NTLMv2 est maintenant requis pour la connexion."
