import json
import pymysql
import re
import os
import time
from datetime import datetime

# Configuration de la base de données
db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "ads",
    "charset": "utf8mb4"
}

# Fonction pour convertir les dates JSON au format MySQL
def convert_json_date(json_date):
    """
    Convertit une date JSON du format /Date(1747383403000)/ en format MySQL 'YYYY-MM-DD HH:MM:SS'.
    Retourne None si la date est absente ou invalide.
    """
    if not json_date or not isinstance(json_date, str):
        return None
    match = re.search(r'/Date\((\d+)\)/', json_date)
    if match:
        timestamp = int(match.group(1)) // 1000
        # Vérifie que le timestamp est raisonnable (exclut 0 ou dates trop anciennes)
        if timestamp > 1000000000:  # ~2001-09-09
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return None

# Connexion à la base de données
def connect_db():
    return pymysql.connect(**db_config)

# Traitement des objets
def process_objects(json_file):
    with open(json_file, 'r', encoding='utf-8-sig') as file:
        data = json.load(file)
    
    groups = data.get("groups", [])
    users = data.get("users", [])
    computers = data.get("computers", [])

    connection = connect_db()
    cursor = connection.cursor()

    # Insérer les groupes dans la table `objectgroup`
    for group in groups:
        try:
            sql = """
                INSERT INTO objectgroup (objectSid, member, distinguishedName, whenChanged, whenCreated, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                member = VALUES(member), distinguishedName = VALUES(distinguishedName), whenChanged = VALUES(whenChanged), whenCreated = VALUES(whenCreated), updated_at = NOW()
            """
            cursor.execute(sql, (
                group["objectSid"],
                group["member"],
                group["distinguishedName"],
                convert_json_date(group["whenChanged"]),
                convert_json_date(group["whenCreated"])
            ))
        except Exception as e:
            print(f"Erreur lors de l'insertion du groupe {group['objectSid']}: {e}")

    # Insérer les utilisateurs dans la table `objectusers`
    for user in users:
        try:
            sql = """
                INSERT INTO ObjectUsers (objectSid, badPasswordTime, lastLogon, lockoutTime, displayName, userPrincipalName, sAMAccountName, distinguishedName, accountExpires, whenChanged, whenCreated, userAccountControl, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FROM_UNIXTIME(%s), %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                displayName = VALUES(displayName), userPrincipalName = VALUES(userPrincipalName), sAMAccountName = VALUES(sAMAccountName), distinguishedName = VALUES(distinguishedName), accountExpires = VALUES(accountExpires), whenChanged = VALUES(whenChanged), whenCreated = VALUES(whenCreated), userAccountControl = VALUES(userAccountControl), updated_at = NOW()
            """
            cursor.execute(sql, (
                user["objectSid"],
                user["badPasswordTime"],
                user["lastlogon"],
                user["lockoutTime"],
                user["DisplayName"],
                user["userPrincipalName"],
                user["sAMAccountName"],
                user["distinguishedName"],
                user["accountExpires"],
                convert_json_date(user["whenChanged"]),
                convert_json_date(user["whenCreated"]),
                user["userAccountControl"]
            ))
        except Exception as e:
            print(f"Erreur lors de l'insertion de l'utilisateur {user['objectSid']}: {e}")

    # Insérer les ordinateurs dans la table `objectcomputers`
    for computer in computers:
        try:
            sql = """
                INSERT INTO objectcomputers (objectSid, logonCount, operatingSystem, distinguishedName, userAccountControl, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                logonCount = VALUES(logonCount), operatingSystem = VALUES(operatingSystem), distinguishedName = VALUES(distinguishedName), userAccountControl = VALUES(userAccountControl), updated_at = NOW()
            """
            cursor.execute(sql, (
                computer["objectSid"],
                computer["logonCount"],
                computer["operatingSystem"],
                computer["distinguishedName"],
                computer["userAccountControl"]
            ))
        except Exception as e:
            print(f"Erreur lors de l'insertion de l'ordinateur {computer['objectSid']}: {e}")

    connection.commit()
    cursor.close()
    connection.close()

    # Supprimer le fichier après traitement
    os.remove(json_file)
    print(f"Fichier {json_file} supprimé après traitement.")

# Main
if __name__ == "__main__":
    objects_dir = "./partage/objects"
    print("Démarrage du traitement périodique des objets...")

    while True:
        for filename in os.listdir(objects_dir):
            if filename.lower().endswith(".json"):
                file_path = os.path.join(objects_dir, filename)
                print(f"Traitement du fichier : {file_path}")
                process_objects(file_path)
        print("Attente de 5 minutes avant le prochain traitement...")
        time.sleep(300)
