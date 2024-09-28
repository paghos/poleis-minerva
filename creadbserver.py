import mysql.connector

# Connection to the MySQL server
conn = mysql.connector.connect(
    host="10.10.10.10",
    port="3308",
    user="user",
    password="random",
    database="minerva_demo"  # Replace with your desired database name
)
cursor = conn.cursor()

# Creazione della tabella AnagraficaPrivato se non esiste
cursor.execute('''
    CREATE TABLE IF NOT EXISTS AnagraficaPrivato (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome TEXT NOT NULL,
        cognome TEXT NOT NULL,
        email TEXT,
        pec TEXT,
        telefono TEXT,
        codicefiscale TEXT,
        idanagrafica TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Creazione della tabella AnagraficaAzienda se non esiste
cursor.execute('''
    CREATE TABLE IF NOT EXISTS AnagraficaAzienda (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ragsociale TEXT,
        email TEXT,
        pec TEXT,
        telefono TEXT,
        piva TEXT,
        idanagrafica TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Creazione della tabella Legale se non esiste
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Legale (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome TEXT,
        cognome TEXT,
        email TEXT,
        pec TEXT,
        telefono TEXT,
        idlegale TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Creazione della tabella Contenzioso se non esiste
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Contenzioso (
        id INT AUTO_INCREMENT PRIMARY KEY,
        numeroprotocollo TEXT,
        dataprotocollo TEXT,
        tipologia TEXT,
        annotributouno TEXT,
        annotributodue TEXT,
        annopresentazione TEXT,
        avvocatoente TEXT,
        autoritagiudiziaria TEXT,
        numerorg TEXT,
        sentenza TEXT,
        oggetto TEXT,
        valore TEXT,
        note TEXT,
        idcontenzioso TEXT,
        idavvocatoente TEXT,
        creato TEXT,
        modificato TEXT,
        datainserimento TEXT,
        datamodifica TEXT,
        operazioneeffettuata TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Creazione della tabella Associazioni se non esiste
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Associazioni (
        id INT AUTO_INCREMENT PRIMARY KEY,
        idanagrafica TEXT,
        idcontenzioso TEXT,
        idlegale TEXT,
        idlegaledue TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Creazione della tabella AutoritaGiudiziarie se non esiste
cursor.execute('''
    CREATE TABLE IF NOT EXISTS AutoritaGiudiziarie (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Creazione della tabella AvvocatiEnte se non esiste
cursor.execute('''
    CREATE TABLE IF NOT EXISTS AvvocatiEnte (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome TEXT,
        cognome TEXT,
        nomecompleto TEXT,
        email TEXT,
        pec TEXT,
        telefono TEXT,
        idavvocatoente TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Creazione della tabella Calendario se non esiste
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Calendario (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nomeevento TEXT,
        data TEXT,
        preavviso TEXT,
        idanagrafica TEXT,
        idcontenzioso TEXT,
        idcalendario TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Commit delle modifiche e chiusura della connessione
conn.commit()
conn.close()

print("Database e tabelle create con successo.")
