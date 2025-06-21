#!/bin/bash

# Variables à personnaliser
DOMAIN_REALM="EXEMPLE.LOCAL"     # Ton domaine AD en majuscules
DOMAIN_NAME="EXEMPLE"            # Workgroup / NetBIOS name en majuscules
DC_FQDN="dc.exemple.local"       # FQDN du contrôleur de domaine
PARTAGE_DIR="/srv/partage"
SAMBA_CONF="/etc/samba/smb.conf"
KRB5_CONF="/etc/krb5.conf"

echo "=== Installation des paquets nécessaires ==="
sudo apt update
sudo apt install -y samba krb5-user winbind libpam-winbind libnss-winbind

# Configuration de Kerberos
echo "=== Configuration de Kerberos (/etc/krb5.conf) ==="
sudo tee "$KRB5_CONF" > /dev/null <<EOF
[libdefaults]
    default_realm = $DOMAIN_REALM
    dns_lookup_realm = false
    dns_lookup_kdc = true

[realms]
    $DOMAIN_REALM = {
        kdc = $DC_FQDN
        admin_server = $DC_FQDN
    }

[domain_realm]
    .$DOMAIN_NAME = $DOMAIN_REALM
    $DOMAIN_NAME = $DOMAIN_REALM
EOF

echo "=== Création du dossier partagé ==="
sudo mkdir -p "$PARTAGE_DIR"
sudo chown root:"$DOMAIN_NAME\Domain Users" "$PARTAGE_DIR" 2>/dev/null || true
sudo chmod 2770 "$PARTAGE_DIR"

# Backup smb.conf si existant
if [ -f "$SAMBA_CONF" ]; then
  sudo cp "$SAMBA_CONF" "${SAMBA_CONF}.bak-$(date +%Y%m%d-%H%M%S)"
fi

echo "=== Configuration de Samba (/etc/samba/smb.conf) ==="
sudo tee "$SAMBA_CONF" > /dev/null <<EOF
[global]
   workgroup = $DOMAIN_NAME
   realm = $DOMAIN_REALM
   security = ADS

   dedicated keytab file = /etc/krb5.keytab
   kerberos method = secrets and keytab

   winbind use default domain = yes
   winbind offline logon = false
   idmap config * : backend = tdb
   idmap config * : range = 10000-20000
   idmap config $DOMAIN_NAME : backend = rid
   idmap config $DOMAIN_NAME : range = 100000-200000

   template shell = /bin/bash
   template homedir = /home/%D/%U

   client signing = yes
   server signing = yes
   client use spnego = yes

   server min protocol = SMB2_02
   server max protocol = SMB3
   client min protocol = SMB2_02
   client max protocol = SMB3
   ntlm auth = ntlmv2-only

[partage]
   path = $PARTAGE_DIR
   read only = no
   browsable = yes
   valid users = @"$DOMAIN_NAME\Domain Users"
   create mask = 0660
   directory mask = 2770
EOF

echo "=== Redémarrage des services Samba et Winbind ==="
sudo systemctl restart smbd nmbd winbind

echo "=== Jonction au domaine Active Directory ==="
read -p "Compte AD avec droits de joindre la machine au domaine (ex: Administrateur) : " AD_USER
sudo net ads join -U "$AD_USER"

if [ $? -eq 0 ]; then
  echo "=== Jonction réussie au domaine ==="
else
  echo "!!! La jonction au domaine a échoué. Vérifie les paramètres et essaie à nouveau."
  exit 1
fi

echo "=== Démarrage / activation des services ==="
sudo systemctl enable smbd nmbd winbind
sudo systemctl restart smbd nmbd winbind

echo "=== Test de récupération de ticket Kerberos ==="
read -p "Utilisateur AD à tester (ex: utilisateur@EXEMPLE.LOCAL) : " TEST_USER
kinit "$TEST_USER"
if klist; then
  echo "✅ Ticket Kerberos obtenu avec succès."
else
  echo "⚠️ Échec d'obtention du ticket Kerberos."
fi

echo "=== ✅ Configuration terminée ==="
echo "➡️  Dossier partagé : \\\\$HOSTNAME\\partage"
echo "➡️  Accès via comptes AD (ex : EXEMPLE\\utilisateur)"
echo "➡️  Kerberos est utilisé pour l'authentification SMB"
echo "✍️  Montez le partage depuis Windows en utilisant un compte AD."
