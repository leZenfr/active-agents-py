import json
import pymysql
import os
import time
from datetime import datetime

# Configuration de la base de données
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "ads",
    "charset": "utf8mb4"
}

# Mapping des EventID vers idEvent
event_mapping = {
    4720: 7,  # Compte créé
    4722: 6,  # Compte activé
    4723: 1,  # Mot de passe modifié
    4725: 2,  # Compte verrouillé
    4738: 9,  # Attributs de compte modifiés
    4731: 3,  # Groupe modifié
    4741: 4,  # PC ajouté
    4756: 5,  # Membre ajouté au groupe
    4757: 8,  # Membre retiré du groupe
    4781: 11, # Changement d'appartenance à un groupe
    4755: 12, # Membre ajouté à un groupe local
    4754: 13, # Membre retiré d’un groupe local
    4727: 17, # Groupe local modifié
    4728: 15, # Membre ajouté à un groupe local
    4737: 16, # Membre retiré d’un groupe local
    4726: 14, # Propriétés du compte utilisateur modifiées
    10: 18    # Connexion anonyme détectée
}

# Fonction pour convertir les dates JSON au format MySQL
def convert_json_date(json_date):
    timestamp = int(json_date.strip("/Date()\\/")) // 1000
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Connexion à la base de données
def connect_db():
    return pymysql.connect(**db_config, cursorclass=pymysql.cursors.DictCursor)

# Récupérer ou créer l'identifierIdLog
def get_identifier_id_log(cursor, event_id):
    id_event = event_mapping.get(event_id)
    if not id_event:
        raise ValueError(f"EventID {event_id} non mappé à un idEvent.")

    cursor.execute("SELECT idIdentifiedLog FROM identifiedlog WHERE idEvent = %s", (id_event,))
    result = cursor.fetchone()
    if result:
        return result["idIdentifiedLog"]

    cursor.execute(
        "INSERT INTO identifiedlog (idEvent, created_at, updated_at) VALUES (%s, NOW(), NOW())",
        (id_event,)
    )
    return cursor.lastrowid

# Traitement des événements
def process_events(json_file):
    with open(json_file, 'r', encoding='utf-8-sig') as file:
        events = json.load(file)

    connection = connect_db()
    cursor = connection.cursor()

    user_event_ids = [4720, 4722, 4723, 4725, 4738, 4726]
    group_event_ids = [4731, 4756, 4757, 4781, 4755, 4754, 4727, 4728, 4737]
    computer_event_ids = [4741]

    for event in events:
        try:
            event_id = event["EventID"]
            time_created = convert_json_date(event["TimeCreated"])
            server_name = event["ServerName"]

            identifier_id_log = get_identifier_id_log(cursor, event_id)

            if event_id in user_event_ids:
                cursor.execute("""
                    SELECT COUNT(*) AS count FROM userlog
                    WHERE identifierIdLog = %s AND targetUserName = %s AND targetSid = %s
                      AND subjectUserSid = %s AND subjectUserName = %s
                """, (
                    identifier_id_log, event["Parameters"].get("Param0"),
                    event["Parameters"].get("Param3"), event["Parameters"].get("Param4"),
                    event["Parameters"].get("Param5")
                ))
                result = cursor.fetchone()

                if result["count"] == 0:
                    sql = """
                        INSERT INTO userlog (
                            identifierIdLog, targetUserName, targetSid, subjectUserSid,
                            subjectUserName, subjectDomainName, subjectLogonId, privilegeList,
                            sAMAccountName, displayName, userPrincipalName, created_at, updated_at
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s
                        )
                    """
                    cursor.execute(sql, (
                        identifier_id_log, event["Parameters"].get("Param0"),
                        event["Parameters"].get("Param3"), event["Parameters"].get("Param4"),
                        event["Parameters"].get("Param5"), event["Parameters"].get("Param6"),
                        event["Parameters"].get("Param7"), event["Parameters"].get("Param8"),
                        event["Parameters"].get("Param9"), event["Parameters"].get("Param10"),
                        event["Parameters"].get("Param11"), time_created, time_created
                    ))
                else:
                    print(f"Événement similaire déjà existant pour l'EventID {event_id} avec targetUserName {event['Parameters'].get('Param0')}")

            elif event_id in group_event_ids:
                sql = """
                    INSERT INTO grouplog (
                        identifierIdLog, targetUserName, targetDomainName, targetSid, subjectUserSid,
                        subjectUserName, subjectLogonId, privilegeList, samAccountName, sidHistory,
                        serverSid, hostname, ipAddress, memberName, memberSid, groupTypeChange,
                        created_at, updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        targetDomainName = VALUES(targetDomainName),
                        subjectUserSid = VALUES(subjectUserSid),
                        subjectUserName = VALUES(subjectUserName),
                        subjectLogonId = VALUES(subjectLogonId),
                        privilegeList = VALUES(privilegeList),
                        samAccountName = VALUES(samAccountName),
                        sidHistory = VALUES(sidHistory),
                        serverSid = VALUES(serverSid),
                        hostname = VALUES(hostname),
                        ipAddress = VALUES(ipAddress),
                        memberName = VALUES(memberName),
                        memberSid = VALUES(memberSid),
                        groupTypeChange = VALUES(groupTypeChange),
                        updated_at = VALUES(updated_at)
                """
                cursor.execute(sql, (
                    identifier_id_log, event["Parameters"].get("Param0"), event["Parameters"].get("Param1"),
                    event["Parameters"].get("Param3"), event["Parameters"].get("Param4"),
                    event["Parameters"].get("Param5"), event["Parameters"].get("Param6"),
                    event["Parameters"].get("Param7"), event["Parameters"].get("Param8"),
                    event["Parameters"].get("Param9"), event["Parameters"].get("Param10"),
                    event["ServerName"], event["ServerIP"], event["Parameters"].get("Param11"),
                    event["Parameters"].get("Param12"), event["Parameters"].get("Param13"),
                    time_created, time_created
                ))

            elif event_id in computer_event_ids:
                sql = """
                    INSERT INTO computerlog (
                        identifierIdLog, computerAccountChange, targetUserName, targetDomainName, targetSid,
                        subjectUserSid, subjectUserName, subjectDomainName, subjectLogonId, privilegeList,
                        samAccountName, displayName, userPrincipalName, homeDirectory, homePath,
                        scriptPath, profilePath, userWorkstations, passwordLastSet, accountExpires,
                        primaryGroupId, allowedToDelegateTo, oldUacValue, newUacValue, userAccountControl,
                        userParameters, sidHistory, logonHours, dnsHostName, servicePrincipalNames,
                        service1, hostname, ipAddress, created_at, updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        computerAccountChange = VALUES(computerAccountChange),
                        targetUserName = VALUES(targetUserName),
                        targetDomainName = VALUES(targetDomainName),
                        targetSid = VALUES(targetSid),
                        subjectUserSid = VALUES(subjectUserSid),
                        subjectUserName = VALUES(subjectUserName),
                        subjectDomainName = VALUES(subjectDomainName),
                        subjectLogonId = VALUES(subjectLogonId),
                        privilegeList = VALUES(privilegeList),
                        samAccountName = VALUES(samAccountName),
                        displayName = VALUES(displayName),
                        userPrincipalName = VALUES(userPrincipalName),
                        homeDirectory = VALUES(homeDirectory),
                        homePath = VALUES(homePath),
                        scriptPath = VALUES(scriptPath),
                        profilePath = VALUES(profilePath),
                        userWorkstations = VALUES(userWorkstations),
                        passwordLastSet = VALUES(passwordLastSet),
                        accountExpires = VALUES(accountExpires),
                        primaryGroupId = VALUES(primaryGroupId),
                        allowedToDelegateTo = VALUES(allowedToDelegateTo),
                        oldUacValue = VALUES(oldUacValue),
                        newUacValue = VALUES(newUacValue),
                        userAccountControl = VALUES(userAccountControl),
                        userParameters = VALUES(userParameters),
                        sidHistory = VALUES(sidHistory),
                        logonHours = VALUES(logonHours),
                        dnsHostName = VALUES(dnsHostName),
                        servicePrincipalNames = VALUES(servicePrincipalNames),
                        service1 = VALUES(service1),
                        hostname = VALUES(hostname),
                        ipAddress = VALUES(ipAddress),
                        updated_at = VALUES(updated_at)
                """
                cursor.execute(sql, (
                    identifier_id_log, event["Parameters"].get("Param0"), event["Parameters"].get("Param1"),
                    event["Parameters"].get("Param3"), event["Parameters"].get("Param4"),
                    event["Parameters"].get("Param5"), event["Parameters"].get("Param6"),
                    event["Parameters"].get("Param7"), event["Parameters"].get("Param8"),
                    event["Parameters"].get("Param9"), event["Parameters"].get("Param10"),
                    event["Parameters"].get("Param11"), event["Parameters"].get("Param12"),
                    event["Parameters"].get("Param13"), event["Parameters"].get("Param14"),
                    event["Parameters"].get("Param15"), event["Parameters"].get("Param16"),
                    event["Parameters"].get("Param17"), event["Parameters"].get("Param18"),
                    event["Parameters"].get("Param19"), event["Parameters"].get("Param20"),
                    event["Parameters"].get("Param21"), event["Parameters"].get("Param22"),
                    event["Parameters"].get("Param23"), event["Parameters"].get("Param24"),
                    event["Parameters"].get("Param25"), event["Parameters"].get("Param26"),
                    event["Parameters"].get("Param27"), event["Parameters"].get("Param28"),
                    event["Parameters"].get("Param29"), event["Parameters"].get("Param30"),
                    event["ServerName"], event["ServerIP"], time_created, time_created
                ))

        except Exception as e:
            print(f"Erreur lors du traitement de l'événement {event_id}: {e}")

    connection.commit()
    cursor.close()
    connection.close()

    # Supprimer le fichier après traitement
    os.remove(json_file)

# Surveillance du répertoire pour traiter les fichiers JSON
def monitor_directory(directory):
    print(f"Surveillance du répertoire : {directory}")
    while True:
        files = [f for f in os.listdir(directory) if f.endswith(".json")]
        for file in files:
            file_path = os.path.join(directory, file)
            print(f"Traitement du fichier : {file}")
            process_events(file_path)
        time.sleep(120)  # Vérifie toutes les 2 minutes

# Main
if __name__ == "__main__":
    directory_to_monitor = "./partage/events"  # Répertoire contenant les fichiers JSON
    monitor_directory(directory_to_monitor)
