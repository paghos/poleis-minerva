import mysql.connector

# Credenziali di accesso al database
db_config = {
    "host": "10.10.10.10",
    "port": "3308",
    "user": "utente",
    "password": "random",
    "database": "minerva_demo"
}

# Lista di autorità giudiziarie da inserire
autorita_giudiziarie = [
    "Corte di giustizia tributaria di I grado di Messina",
    "Corte di giustizia tributaria di I grado di Catania",
    "Corte di giustizia tributaria di II grado di Messina",
    "Corte di giustizia tributaria di II grado di Catania",
    "Corte di giustizia tributaria di II grado di Palermo",
    "Tribunale di Messina",
    "Tribunale di Catania",
    "Giudice di pace di Messina",
    "Giudice di pace di Catania",
    "Giudice di pace di Giarre",
]

# Funzione per popolare la tabella
def popola_tabella_autorita_giudiziaria(conn, autorita_giudiziarie):
    try:
        cursor = conn.cursor()
        for autorita in autorita_giudiziarie:
            query = "INSERT INTO AutoritaGiudiziarie (nome) VALUES (%s)"
            values = (autorita,)
            cursor.execute(query, values)

        conn.commit()
        print("Dati inseriti correttamente nella tabella AutoritaGiudiziaria.")
    except Exception as e:
        print(f"Errore durante l'inserimento dei dati: {e}")
    finally:
        cursor.close()

# Connessione al database e chiamata alla funzione di popolamento
try:
    conn = mysql.connector.connect(**db_config)
    popola_tabella_autorita_giudiziaria(conn, autorita_giudiziarie)
except mysql.connector.Error as err:
    print(f"Errore di connessione al database: {err}")
finally:
    if conn.is_connected():
        conn.close()
        print("Connessione al database chiusa.")
