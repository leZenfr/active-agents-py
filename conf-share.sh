#!/bin/bash

echo "=== Configuration Samba + Kerberos AD automatique ==="

read -p "Domaine Kerberos (ex: EXEMPLE.LOCAL) : " DOMAIN_REALM
DOMAIN_REALM=${DOMAIN_REALM^^}  # majuscules

read -p "Nom NetBIOS / Workgroup (ex: EXEMPLE) : " DOMAIN_NAME
DOMAIN_NAME=${DOMAIN_NAME^^}  # majuscules

read -p "FQDN du contrôleur de domaine (ex: dc.exemple.local) : " DC_FQDN

read -p "Dossier à partager (par défaut /srv/partage) : " PARTAGE_DIR
PARTAGE_DIR=${PARTAGE_DIR:-/srv/partage}

SAMBA_CONF="/etc/samba/smb.conf"
KRB5_CONF="/etc/krb5.conf"

echo "=== Installation des paquets nécessaires ==="
sudo apt update
sudo apt install -y samba krb5-user winbind libpam-winbind libnss-winbind

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
read -p "Compte AD avec droits pour joindre la machine au domaine (ex: Administrateur) : " AD_USER
sudo net ads join -U "$AD_USER"

if [ $? -eq 0 ]; then
  echo "✅ Jonction réussie au domaine"
else
  echo "❌ Échec de la jonction au domaine. Vérifiez les paramètres et réessayez."
  exit 1
fi

echo "=== Démarrage / activation des services ==="
sudo systemctl enable smbd nmbd winbind
sudo systemctl restart smbd nmbd winbind

echo "=== Test de récupération de ticket Kerberos ==="
read -p "Utilisateur AD à tester (ex: utilisateur@$DOMAIN_REALM) : " TEST_USER
kinit "$TEST_USER"
if klist; then
  echo "✅ Ticket Kerberos obtenu avec succès."
else
  echo "⚠️ Échec d'obtention du ticket Kerberos."
fi

echo "=== ✅ Configuration terminée ==="
echo "➡️  Dossier partagé : \\\\$HOSTNAME\\partage"
echo "➡️  Accès via comptes AD (ex : $DOMAIN_NAME\\utilisateur)"
echo "➡️  Kerberos est utilisé pour l'authentification SMB"
echo "✍️  Montez le partage depuis Windows en utilisant un compte AD."
