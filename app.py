from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort, send_file, send_from_directory, g, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_, case, text, create_engine, Column, String, Integer
from datetime import datetime, timedelta
import string
import secrets
import logging
import os
import zipfile
import uuid
import json
import requests
import msal
import app_config
from flask_session import Session
from waitress import serve
from calendar import monthrange, monthcalendar
import calendar
import locale
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
import io
import sys
from minervaconfig import appConf, database, ai

locale.setlocale(locale.LC_TIME, 'it_IT.utf8')

app = Flask(__name__)
app.config.from_object(app_config)
Session(app)

app.config['SQLALCHEMY_DATABASE_URI'] = database.get("DATABASE_CONFIG")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = appConf.get("FLASK_SECRET")

oauth = OAuth(app)
keycloak = oauth.register(
    "keycloak",
    client_id=appConf.get("OAUTH2_CLIENT_ID"),
    client_secret=appConf.get("OAUTH2_CLIENT_SECRET"),
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url=f'{appConf.get("OAUTH2_ISSUER")}/.well-known/openid-configuration',
    )

MINERVA_AI_ENDPOINT = ai.get("MINERVA_AI_ENDPOINT")

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

db = SQLAlchemy(app)

def generate_random_code():
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(8))

class AnagraficaPrivato(db.Model):
    __tablename__ = 'AnagraficaPrivato'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=True)
    pec = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(20), nullable=False)
    codicefiscale = db.Column(db.String(16), nullable=True)
    idanagrafica = db.Column(db.String(10), nullable=False)
    
class AnagraficaAzienda(db.Model):
    __tablename__ = 'AnagraficaAzienda'
    id = db.Column(db.Integer, primary_key=True)
    ragsociale = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=True)
    pec = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(20), nullable=False)
    piva = db.Column(db.String(20), nullable=True)
    idanagrafica = db.Column(db.String(10), nullable=False)
    
class Legale(db.Model):
    __tablename__ = 'Legale'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=True)
    pec = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(20), nullable=False)
    idlegale = db.Column(db.String(10), nullable=False)

class Contenzioso(db.Model):
    __tablename__ = 'Contenzioso'
    id = db.Column(db.Integer, primary_key=True)
    numeroprotocollo = db.Column(db.String(15), nullable=False)
    dataprotocollo = db.Column(db.String(500), nullable=False)
    tipologia = db.Column(db.String(100), nullable=False)
    annotributouno = db.Column(db.String(4), nullable=False)
    annotributodue = db.Column(db.String(4), nullable=False)
    annopresentazione = db.Column(db.String(200), nullable=True)
    avvocatoente = db.Column(db.String(200), nullable=True)
    autoritagiudiziaria = db.Column(db.String(10), nullable=False)
    numerorg = db.Column(db.String(10), nullable=False)
    sentenza = db.Column(db.String(10), nullable=False)
    oggetto = db.Column(db.String(10), nullable=False)
    valore = db.Column(db.String(10), nullable=False)
    note = db.Column(db.String(10), nullable=False)
    idcontenzioso = db.Column(db.String(10), nullable=False)
    idavvocatoente = db.Column(db.String(10), nullable=False)
    creato = db.Column(db.String(100), nullable=False)
    modificato = db.Column(db.String(100), nullable=False)
    datainserimento = db.Column(db.String(100), nullable=False)
    datamodifica = db.Column(db.String(100), nullable=False)
    operazioneeffettuata = db.Column(db.String(1000), nullable=False)

class Associazioni(db.Model):
    __tablename__ = 'Associazioni'
    id = db.Column(db.Integer, primary_key=True)
    idcontenzioso = db.Column(db.String(10), nullable=False)
    idanagrafica = db.Column(db.String(10), nullable=False)
    idlegale = db.Column(db.String(10), nullable=False)
    idlegaledue = db.Column(db.String(10), nullable=False)
    
class AvvocatiEnte(db.Model):
    __tablename__ = 'AvvocatiEnte'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    nomecompleto = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    pec = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(100), nullable=False)
    idavvocatoente = db.Column(db.String(10), nullable=True)
  
class AutoritaGiudiziarie(db.Model):
    __tablename__ = 'AutoritaGiudiziarie'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

class Calendario(db.Model):
    __tablename__ = 'Calendario'
    id = db.Column(db.Integer, primary_key=True)
    nomeevento = db.Column(db.String(200), nullable=False)
    data = db.Column(db.String(100), nullable=False)
    preavviso = db.Column(db.String(100), nullable=True)
    idanagrafica = db.Column(db.String(10), nullable=False)
    idcontenzioso = db.Column(db.String(10), nullable=False)
    idcalendario = db.Column(db.String(10), nullable=False)

@app.before_request
def check_user_logged_in():

    if request.path in ['/login', '/authorize']:
        return
    if 'oauth_token' not in session:
        return redirect('/login')

@app.route('/login')
def login():
    nonce = secrets.token_urlsafe()
    session['nonce'] = nonce
    redirect_uri = url_for('authorize', _external=True)
    return keycloak.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/authorize')
def authorize():
    try:
        token = keycloak.authorize_access_token()
        session['oauth_token'] = token
        nonce = session.pop('nonce', None)
        user_info = keycloak.parse_id_token(token, nonce=nonce)
        session['user_name'] = user_info.get('name')
        session['user_email'] = user_info.get('email')
        session['user_preferred_username'] = user_info.get('preferred_username')
        return redirect(url_for('index'))
    except Exception as e:
        return f"ATTENZIONE! Errore nell'autenticazione, comunicare questo messaggio di errore all'amministratore di sistema.  {e} "
    

@app.route('/logout')
def logout():
    session.pop('oauth_token', None)  
    
    keycloak_logout_url = f'{appConf.get("OAUTH2_ISSUER")}/protocol/openid-connect/logout'
    client_id = 'account'

    logout_url = f"{keycloak_logout_url}?client_id={client_id}"
    return redirect(logout_url)


@app.route('/', methods=['GET', 'POST'])
def index():
    utente = session.get('user_name')
    
    contenziosi = Contenzioso.query.all()
    anagrafica_privato = AnagraficaPrivato.query.all()
    anagrafica_azienda = AnagraficaAzienda.query.all()
        
    somma_totale = 0

    for contenzioso in contenziosi:
        valore = float(contenzioso.valore)  
        somma_totale += valore


    somma_totale = round(somma_totale, 2)


    numero_contenziosi = Contenzioso.query.filter(Contenzioso.idcontenzioso.isnot(None)).count()
    numero_anagrafiche = AnagraficaAzienda.query.filter(AnagraficaAzienda.idanagrafica.isnot(None)).count() + AnagraficaPrivato.query.filter(AnagraficaPrivato.idanagrafica.isnot(None)).count()    
    
    contenziosi_rg = Contenzioso.query.filter(Contenzioso.numerorg.isnot(None)).count()
    
    
    print("Dashboard_valore",somma_totale)
    print("Numero_anagrafiche",numero_anagrafiche)
    print("Numero_Contenziosi",numero_contenziosi)


    return render_template('index.html',somma_totale=somma_totale,
                           numero_anagrafiche=numero_anagrafiche,
                           numero_contenziosi=numero_contenziosi,
                           contenziosi_rg=contenziosi_rg, user=utente)
    
@app.route('/anagrafica_privato', methods=['GET', 'POST'])
def anagrafica_privato():

    utente = session.get('user_name')
    
    if request.method == 'POST':
            codicefiscale = request.form['codicefiscale'].upper()
            nome = request.form['nome'].title()
            cognome = request.form['cognome'].title()
            email = request.form['email']
            pec = request.form['pec']
            telefono = request.form['telefono']
            idanagrafica = "PP" + generate_random_code()

            anagraficaprivato = AnagraficaPrivato(
                nome=nome, cognome=cognome, email=email, pec=pec, telefono=telefono,
                codicefiscale=codicefiscale,  idanagrafica=idanagrafica)

            anagrafica_esistente = AnagraficaPrivato.query.filter(or_(AnagraficaPrivato.codicefiscale == codicefiscale,
                                                                    and_(AnagraficaPrivato.nome == nome,
                                                                        AnagraficaPrivato.cognome == cognome))).first()

            if anagrafica_esistente:
                return redirect(url_for('riepilogo_privato', idanagrafica=anagrafica_esistente.idanagrafica))
        
            db.session.add(anagraficaprivato)
            db.session.commit()
            return redirect(url_for('riepilogo_privato', idanagrafica=idanagrafica))

    return render_template('anagrafica_privato.html',user=utente)

@app.route('/ricerca_anagrafica_privato', methods=['GET','POST'])
def ricerca_anagrafica_privato():

    utente = session.get('user_name')

    if request.method == 'POST':
        codicefiscale = request.form['codicefiscale']
        nome = request.form['nome']
        cognome = request.form['cognome']

        anagrafica_esistente = AnagraficaPrivato.query.filter(or_(AnagraficaPrivato.codicefiscale == codicefiscale,
                                                                and_(AnagraficaPrivato.nome == nome,
                                                                    AnagraficaPrivato.cognome == cognome))).first()

        if anagrafica_esistente:

         return redirect(url_for('riepilogo_privato', idanagrafica=anagrafica_esistente.idanagrafica))
        else:
            return render_template('anagrafica_non_trovata.html', user=utente)
    
    return render_template('ricerca_anagrafica_privato.html', user=utente)


@app.route('/anagrafica_azienda', methods=['GET', 'POST'])
def anagrafica_azienda():


    utente = session.get('user_name')    
    
    if request.method == 'POST':
            ragsociale = request.form['ragsociale'].title()
            email = request.form['email']
            pec = request.form['pec']
            telefono = request.form['telefono']
            piva = request.form['piva']
            idanagrafica = "AZ"+generate_random_code()

            anagraficaazienda = AnagraficaAzienda(ragsociale=ragsociale, email=email, pec=pec, telefono=telefono,
                                        piva=piva, idanagrafica=idanagrafica)
            
            anagrafica_esistente = AnagraficaAzienda.query.filter(or_(AnagraficaAzienda.piva == piva,
                                                          AnagraficaAzienda.ragsociale == ragsociale)).first()

            if anagrafica_esistente:

                 return redirect(url_for('riepilogo_azienda', idanagrafica=anagrafica_esistente.idanagrafica))
            
            db.session.add(anagraficaazienda)
            db.session.commit()
            return redirect(url_for('riepilogo_azienda', idanagrafica=idanagrafica))

    return render_template('anagrafica_azienda.html',user=utente)

@app.route('/ricerca_anagrafica_azienda', methods=['GET','POST'])
def ricerca_anagrafica_azienda():

    utente = session.get('user_name')

    if request.method == 'POST':
        piva = request.form['piva']
        ragsociale = request.form['ragsociale']


        anagrafica_esistente = AnagraficaAzienda.query.filter(or_(AnagraficaAzienda.piva == piva,
                                                          AnagraficaAzienda.ragsociale == ragsociale)).first()

        if anagrafica_esistente:

         return redirect(url_for('riepilogo_azienda', idanagrafica=anagrafica_esistente.idanagrafica))
        else:
            return render_template('anagrafica_non_trovata.html', user=utente)


    return render_template('ricerca_anagrafica_azienda.html', user=utente)


@app.route('/anagrafica_legale', methods=['GET', 'POST'])
def anagrafica_legale():


    utente = session.get('user_name')
    
    if request.method == 'POST':
            nome = request.form['nome']
            cognome = request.form['cognome']
            email = request.form['email']
            pec = request.form['pec']
            telefono = request.form['telefono']
            idlegale = "LL"+generate_random_code()

            anagraficalegale = Legale(nome=nome, cognome=cognome, email=email, pec=pec, telefono=telefono, idlegale=idlegale)

            anagrafica_esistente = Legale.query.filter(and_(Legale.pec == pec,
                                                            Legale.nome == nome,
                                                            Legale.cognome == cognome)).first()

            if anagrafica_esistente:

                return redirect(url_for('riepilogo_legale', idlegale=anagrafica_esistente.idlegale, user=utente))

            db.session.add(anagraficalegale)
            db.session.commit()
                 
            return redirect(url_for('riepilogo_legale', idlegale=idlegale, user=utente))

    return render_template('anagrafica_legale.html', user=utente)

@app.route('/ricerca_anagrafica_legale', methods=['GET','POST'])
def ricerca_anagrafica_legale():


    utente = session.get('user_name')
    
    if request.method == 'POST':
        pec = request.form['pec']
        nome = request.form['nomelegale']
        cognome = request.form['cognomelegale']

        anagrafica_esistente = Legale.query.filter(and_(Legale.pec == pec,
                                                        Legale.nome == nome,
                                                        Legale.cognome == cognome)).first()

        if anagrafica_esistente:

         return redirect(url_for('riepilogo_legale', idlegale=anagrafica_esistente.idlegale, user=utente))
        else:
            return render_template('anagrafica_non_trovata.html', user=utente)
         
    return render_template('ricerca_anagrafica_legale.html', user=utente)

@app.route('/anagrafica_avvocato_ente', methods=['GET', 'POST'])
def anagrafica_avvocato_ente():


    utente = session.get('user_name')
    
    if request.method == 'POST':
            nome = request.form['nome']
            cognome = request.form['cognome']
            email = request.form['email']
            pec = request.form['pec']
            telefono = request.form['telefono']
            idavvocatoente = "AE"+generate_random_code()

            nomecompleto = nome.title() + " " + cognome.title()
            
            avvocatoente = AvvocatiEnte(nome=nome, cognome=cognome, email=email, pec=pec, telefono=telefono, idavvocatoente=idavvocatoente, nomecompleto=nomecompleto)
            
            db.session.add(avvocatoente)
            db.session.commit()
    
            return redirect(url_for('riepilogo_avvocato_ente', idavvocatoente=idavvocatoente))
            
    return render_template('anagrafica_avvocato_ente.html',user=utente)

@app.route('/ricerca_anagrafica_avvocato_ente', methods=['GET','POST'])
def ricerca_anagrafica_avvocato_ente():


    utente = session.get('user_name')
    
    if request.method == 'POST':
        idavvocatoente = request.form['idavvocatoente']
        
        anagrafica_esistente = AvvocatiEnte.query.filter_by(idavvocatoente=idavvocatoente).first()


        if anagrafica_esistente:

         return redirect(url_for('riepilogo_avvocato_ente', idavvocatoente=anagrafica_esistente.idavvocatoente))
        else:
            return render_template('anagrafica_non_trovata.html', user=utente)

    return render_template('ricerca_avvocato_ente.html',user=utente)


@app.route('/nuovo_contenzioso', methods=['GET', 'POST'])
def nuovo_contenzioso():

    utente = session.get('user_name')
    
    retrieved_idanagrafica = request.args.get('idanagrafica')

    ai_annotributodue = request.args.get('ai_annotributodue')
    ai_annotributouno = request.args.get('ai_annotributouno')
    ai_dataprotocollo = request.args.get('ai_dataprotocollo')
    ai_idavvocatoente = request.args.get('ai_idavvocatoente')
    ai_message = request.args.get('ai_message')
    ai_nomecompletoavvocatoente = request.args.get('ai_nomecompletoavvocatoente')
    ai_numeroprotocollo = request.args.get('ai_numeroprotocollo')
    ai_oggetto = request.args.get('ai_oggetto')
    ai_pec = request.args.get('ai_pec')
    ai_tipologia = request.args.get('ai_tipologia')
    ai_valore = request.args.get('ai_valore')

    print(retrieved_idanagrafica)

    if request.method == 'POST':
        pec = request.form['pec']
        pecdue = request.form['pecdue']
        
        idlegaledue = ""

        anagrafica_legale_esistente = Legale.query.filter(or_(Legale.pec == pec)).first()

        if anagrafica_legale_esistente:
            idlegale = anagrafica_legale_esistente.idlegale
            print("IDLEGALE: ", idlegale)
        else:
            nome = request.form['nomelegale']
            cognome = request.form['cognomelegale']
            email = request.form['emaillegale']
            pec = request.form['pec']
            telefono = request.form['telefonolegale']
            idlegale = "LL" + generate_random_code()

            anagraficalegale = Legale(nome=nome, cognome=cognome, email=email, pec=pec, telefono=telefono, idlegale=idlegale)

            db.session.add(anagraficalegale)
            db.session.commit()

        if request.form['nomelegaledue']: 
            cognome = request.form['cognomelegaledue']
            email = request.form['emaillegaledue']
            pec = request.form['pecdue']
            telefono = request.form['telefonolegaledue']
            idlegaledue = "LL" + generate_random_code()

            anagraficalegale_due = Legale(nome=request.form['nomelegaledue'], cognome=cognome, email=email, pec=pec, telefono=telefono, idlegale=idlegaledue)

            db.session.add(anagraficalegale_due)
            db.session.commit()

        numeroprotocollo = request.form['numeroprotocollo']
        dataprotocollo = request.form['dataprotocollo']
        tipologia = request.form['tipologia']
        annotributouno = request.form['annotributouno']
        annotributodue = request.form['annotributodue']
        annopresentazione = request.form['annopresentazione']
        avvocatoente = request.form['nomecompletoavvocatoente']
        autoritagiudiziaria = request.form['autoritagiudiziaria']
        numerorg = request.form['numerorg']
        if not numerorg:
            numerorg = ""
        dataudienza_str = request.form['dataudienza']
        dataudienza = datetime.strptime(dataudienza_str, '%Y-%m-%d')

        dataudienza = dataudienza.replace(hour=0, minute=0, second=0)

        preavvisoudienza = dataudienza - timedelta(days=22)
        sentenza = request.form['sentenza']
        oggetto = request.form['oggetto']
        valore = request.form['valore']
        note = request.form['note']
        idcontenzioso = "CZ" + generate_random_code()
        idcalendario = "CL" + generate_random_code()
        idanagrafica = request.form['idanagrafica']
        idavvocatoente = request.form['idavvocatoente']
        creato=utente
        modificato=""
        datamodifica=""
        datainserimento=datetime.now().strftime('%d/%m/%Y %H:%M')
        operazioneeffettuata="Aggiunta del contenzioso."
        
        contenzioso = Contenzioso(tipologia=tipologia, annotributouno=annotributouno, annotributodue=annotributodue,
                                    annopresentazione=annopresentazione, avvocatoente=avvocatoente,
                                    autoritagiudiziaria=autoritagiudiziaria, numerorg=numerorg, 
                                    sentenza=sentenza, oggetto=oggetto, valore=valore, note=note,
                                    idcontenzioso=idcontenzioso, numeroprotocollo=numeroprotocollo,
                                    dataprotocollo=dataprotocollo, idavvocatoente=idavvocatoente, 
                                    creato=creato, datainserimento=datainserimento, operazioneeffettuata=operazioneeffettuata,
                                    datamodifica=datamodifica, modificato=modificato)
        db.session.add(contenzioso)
        db.session.commit()
        
        tp_ragsociale = None
        tp_nomecompleto = None
        
        if idanagrafica is not None:
            if idanagrafica.startswith("AZ"):
                anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_azienda:
                    tp_ragsociale = anagrafica_azienda.ragsociale
            elif idanagrafica.startswith("PP"):  
                anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_privato:
                    tp_nome = anagrafica_privato.nome
                    tp_cognome = anagrafica_privato.cognome
                    tp_nomecompleto = tp_nome + " " + tp_cognome
            else:
                return "Formato idanagrafica non valido."

        if tp_ragsociale is not None:
                nomeevento = tp_ragsociale
        elif tp_nomecompleto is not None:
                nomeevento = tp_nomecompleto
        
        calendario = Calendario(nomeevento=nomeevento, data=dataudienza, preavviso=preavvisoudienza,
                                    idcontenzioso=idcontenzioso, idcalendario=idcalendario,
                                    idanagrafica=idanagrafica)
        db.session.add(calendario)
        db.session.commit()
        
        print("IDLEGALEDUE: ", idlegaledue)
        associazioni = Associazioni(idanagrafica=idanagrafica, idcontenzioso=idcontenzioso, idlegale=idlegale, idlegaledue=idlegaledue)
        db.session.add(associazioni)
        db.session.commit()
        return redirect(url_for('contenzioso', idcontenzioso=idcontenzioso,user=utente))

    values = {
            'ai_annotributodue': ai_annotributodue or '',
            'ai_annotributouno': ai_annotributouno or '',
            'ai_dataprotocollo': ai_dataprotocollo or '',
            'ai_idavvocatoente': ai_idavvocatoente or '',
            'ai_message': ai_message or '',
            'ai_nomecompletoavvocatoente': ai_nomecompletoavvocatoente or '',
            'ai_numeroprotocollo': ai_numeroprotocollo or '',
            'ai_oggetto': ai_oggetto or '',
            'ai_pec': ai_pec or '',
            'ai_tipologia': ai_tipologia or '',
            'ai_valore': ai_valore or ''
        }
    return render_template('nuovo_contenzioso.html', user=utente, **values)


@app.route('/calendario_udienze', methods=['GET'])
def calendario_udienze():


    utente = session.get('user_name')
    
    today = datetime.today()

    year = int(request.args.get('year', datetime.today().year))
    month = int(request.args.get('month', datetime.today().month))

    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    eventi = Calendario.query.all()

    month_name = calendar.month_name[month]

    cal = calendar.monthcalendar(year, month)

    print("Year:", year, eventi)


    return render_template('calendario_udienze.html', eventos=eventi, user=utente, month=month, year=year)

@app.route('/search_legal', methods=['GET'])
def search_legal():

    utente = session.get('user_name')
    
    pec = request.args.get('pec')
    legali = Legale.query.filter(Legale.pec.like(f'%{pec}%')).all()
    
    results = [{'nome': legale.nome, 'cognome': legale.cognome, 'pec': legale.pec, 'telefono': legale.telefono, 'email': legale.email} for legale in legali]
    return jsonify(results)

@app.route('/cerca_anagrafica_privato', methods=['GET'])
def cerca_anagrafica_privato():


    utente = session.get('user_name')
    
    nome = request.args.get('nome')
    cognome = request.args.get('cognome')
    print(nome,cognome)
    anagrafica_privato_list = AnagraficaPrivato.query.filter(AnagraficaPrivato.nome.like(f'%{nome}%'), AnagraficaPrivato.cognome.like(f'%{cognome}%')).all()


    results = [{'nome': anagrafica.nome, 'cognome': anagrafica.cognome, 'pec': anagrafica.pec,
                'telefono': anagrafica.telefono, 'email': anagrafica.email, 'codicefiscale': anagrafica.codicefiscale} for anagrafica in anagrafica_privato_list]

    return jsonify(results)

@app.route('/cerca_anagrafica_azienda', methods=['GET'])
def cerca_anagrafica_azienda():


    utente = session.get('user_name')
    
    ragsociale = request.args.get('ragsociale')

    anagrafica_azienda_list = AnagraficaAzienda.query.filter(AnagraficaAzienda.ragsociale.like(f'%{ragsociale}%')).all()
    
    results = [{'ragsociale': anagrafica.ragsociale, 'piva': anagrafica.piva, 'pec': anagrafica.pec,
                'telefono': anagrafica.telefono, 'email': anagrafica.email} for anagrafica in anagrafica_azienda_list]

    return jsonify(results)

@app.route('/cerca_autorita_giudiziaria', methods=['GET'])
def cerca_autorita_giudiziaria():


    utente = session.get('user_name')
    
    autorita = request.args.get('autorita')
    autoritagiudiziarie = AutoritaGiudiziarie.query.filter(AutoritaGiudiziarie.nome.like(f'%{autorita}%')).all()
    
    results = [{'nome': autoritagiudiziaria.nome} for autoritagiudiziaria in autoritagiudiziarie]
    return jsonify(results)

@app.route('/cerca_avvocato_ente', methods=['GET'])
def cerca_avvocato_ente():


    utente = session.get('user_name')
        
    nomecompleto = request.args.get('nomecompleto')
    avvocatiente = AvvocatiEnte.query.filter(AvvocatiEnte.nomecompleto.like(f'%{nomecompleto}%')).all()
    
    results = [{'nome': avvocatiente.nome, 'cognome': avvocatiente.cognome, 'pec': avvocatiente.pec, 'telefono': avvocatiente.telefono, 'email': avvocatiente.email, 'nomecompleto': avvocatiente.nomecompleto, 'idavvocatoente': avvocatiente.idavvocatoente} for avvocatiente in avvocatiente]
    return jsonify(results)

@app.route('/riepilogo_privato', methods=['GET'])
def riepilogo_privato():


    utente = session.get('user_name')
    
    retrieved_idanagrafica = request.args.get('idanagrafica')

    anagrafica_esistente = AnagraficaPrivato.query.filter_by(idanagrafica=retrieved_idanagrafica).first()
    
    if anagrafica_esistente:
        tp_nome = anagrafica_esistente.nome
        tp_cognome = anagrafica_esistente.cognome
        tp_email = anagrafica_esistente.email
        tp_pec = anagrafica_esistente.pec
        tp_telefono = anagrafica_esistente.telefono
        tp_codicefiscale = anagrafica_esistente.codicefiscale
        tp_idanagrafica = anagrafica_esistente.idanagrafica
        
        associazioni = Associazioni.query.filter_by(idanagrafica=anagrafica_esistente.idanagrafica).all()

        print("RICERCA_IDANAGRAFICA: ", anagrafica_esistente.idanagrafica)
        print("RICERCA_ASSOCIAZIONITROVATE:", associazioni)

        contenziosi = []
        for associazione in associazioni:
            contenzioso = Contenzioso.query.filter_by(idcontenzioso=associazione.idcontenzioso).first()
            if contenzioso:
                contenziosi.append(contenzioso)

        return render_template('riepilogo_privato.html',user=utente , contenziosi=contenziosi, tp_idanagrafica = tp_idanagrafica,tp_nome=tp_nome, tp_cognome=tp_cognome, tp_email=tp_email, tp_pec=tp_pec, tp_telefono=tp_telefono, tp_codicefiscale=tp_codicefiscale)

    else:
        return "Anagrafica non trovata."

@app.route('/riepilogo_azienda', methods=['GET'])
def riepilogo_azienda():


    utente = session.get('user_name')
    
    retrieved_idanagrafica = request.args.get('idanagrafica')
 
    anagrafica_esistente = AnagraficaAzienda.query.filter_by(idanagrafica=retrieved_idanagrafica).first()
    
    if anagrafica_esistente:
        tp_ragsociale = anagrafica_esistente.ragsociale
        tp_email = anagrafica_esistente.email
        tp_pec = anagrafica_esistente.pec
        tp_telefono = anagrafica_esistente.telefono
        tp_piva = anagrafica_esistente.piva
        tp_idanagrafica = anagrafica_esistente.idanagrafica
        
        associazioni = Associazioni.query.filter_by(idanagrafica=anagrafica_esistente.idanagrafica).all()

        print("RICERCA_IDANAGRAFICA: ", anagrafica_esistente.idanagrafica)
        print("RICERCA_ASSOCIAZIONITROVATE:", associazioni)

        contenziosi = []
        for associazione in associazioni:
            contenzioso = Contenzioso.query.filter_by(idcontenzioso=associazione.idcontenzioso).first()
            if contenzioso:
                contenziosi.append(contenzioso)

        return render_template('riepilogo_azienda.html', user=utente , contenziosi=contenziosi, tp_idanagrafica = tp_idanagrafica,tp_ragsociale=tp_ragsociale,  tp_email=tp_email, tp_pec=tp_pec, tp_telefono=tp_telefono, tp_piva=tp_piva)

    else:
        return "Anagrafica non trovata. Verifica la correttezza dei dati immessi."

@app.route('/riepilogo_legale', methods=['GET'])
def riepilogo_legale():


    utente = session.get('user_name')
    
    contenziosi_with_idanagrafica = []
    anno = None
    autoritagiudiziaria = None
    
    retrieved_idlegale = request.args.get('idlegale')
    anagrafica_esistente = Legale.query.filter_by(idlegale=retrieved_idlegale).first()
    
    contenziosi = Associazioni.query.filter((Associazioni.idlegale == retrieved_idlegale) | (Associazioni.idlegaledue == retrieved_idlegale)).all()
    for associazione in Associazioni.query.filter((Associazioni.idlegale == retrieved_idlegale) | (Associazioni.idlegaledue == retrieved_idlegale)).all():
        contenzioso = Contenzioso.query.filter_by(idcontenzioso=associazione.idcontenzioso).first()
        idcontenzioso = contenzioso.idcontenzioso
        
        retrieve_idanagrafica = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
        
        if associazione:
            idanagrafica = retrieve_idanagrafica.idanagrafica
            
            print("ANAGRAFICA:", idanagrafica)
            
            if idanagrafica.startswith("AZ"):
                anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_azienda:
                    tp_nome=""
                    tp_cognome=""
                    tp_codicefiscale=""
                    tp_ragsociale = anagrafica_azienda.ragsociale
                    print("TrovataRAGSOCIALE", tp_ragsociale)
                    tp_email = anagrafica_azienda.email
                    tp_pec = anagrafica_azienda.pec
                    tp_telefono = anagrafica_azienda.telefono
                    tp_piva = anagrafica_azienda.piva
                    tp_idanagraficaazienda = anagrafica_azienda.idanagrafica
                    
            elif idanagrafica.startswith("PP"):
                anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_privato:
                    tp_ragsociale=""
                    tp_piva=""
                    tp_nome = ""
                    tp_nome = anagrafica_privato.nome
                    tp_cognome = anagrafica_privato.cognome
                    tp_email = anagrafica_privato.email
                    tp_pec = anagrafica_privato.pec
                    tp_telefono = anagrafica_privato.telefono
                    tp_codicefiscale = anagrafica_privato.codicefiscale
                    tp_idanagraficaprivato = anagrafica_privato.idanagrafica
                    
            else:
                return "Formato idanagrafica non valido."
        else:
            idanagrafica = None


        idcontenzioso=contenzioso.idcontenzioso
        
        
        contenziosi_with_idanagrafica.append((contenzioso, tp_nome, tp_cognome, tp_ragsociale, idanagrafica))


    return render_template('riepilogo_legale.html',anagrafica_esistente=anagrafica_esistente, tp_nome=tp_nome, tp_cognome=tp_cognome, tp_email=tp_email, tp_pec=tp_pec, tp_telefono=tp_telefono, contenziosi=contenziosi_with_idanagrafica,
                            user=utente)


@app.route('/riepilogo_avvocato_ente', methods=['GET'])
def riepilogo_avvocato_ente():


    utente = session.get('user_name')
    
    contenziosi_with_idanagrafica = []
    anno = None
    autoritagiudiziaria = None
    
    retrieved_idavvocatoente = request.args.get('idavvocatoente')
    anagrafica_esistente = AvvocatiEnte.query.filter_by(idavvocatoente=retrieved_idavvocatoente).first()

    tp_nome=""
    tp_cognome=""
    tp_codicefiscale=""
    tp_ragsociale=""
    tp_piva=""
 
    contenziosi = Contenzioso.query.filter(Contenzioso.idavvocatoente == retrieved_idavvocatoente).all()
    for contenzioso in contenziosi:

        idavvocatoente = contenzioso.idavvocatoente
        idcontenzioso = contenzioso.idcontenzioso
        associazione = db.session.query(Contenzioso).filter_by(idavvocatoente=idavvocatoente, idcontenzioso=idcontenzioso).first()
        retrieve_idanagrafica = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
        
        if associazione:
            idanagrafica = retrieve_idanagrafica.idanagrafica
            print("ANAGRAFICA:", idanagrafica)
            
            if idanagrafica.startswith("AZ"):
                anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_azienda:
                    tp_nome=""
                    tp_cognome=""
                    tp_codicefiscale=""
                    tp_ragsociale = anagrafica_azienda.ragsociale
                    print("TrovataRAGSOCIALE", tp_ragsociale)
                    tp_email = anagrafica_azienda.email
                    tp_pec = anagrafica_azienda.pec
                    tp_telefono = anagrafica_azienda.telefono
                    tp_piva = anagrafica_azienda.piva
                    tp_idanagraficaazienda = anagrafica_azienda.idanagrafica
                    
            elif idanagrafica.startswith("PP"):
                anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_privato:
                    tp_ragsociale=""
                    tp_piva=""
                    tp_nome = anagrafica_privato.nome
                    tp_cognome = anagrafica_privato.cognome
                    tp_email = anagrafica_privato.email
                    tp_pec = anagrafica_privato.pec
                    tp_telefono = anagrafica_privato.telefono
                    tp_codicefiscale = anagrafica_privato.codicefiscale
                    tp_idanagraficaprivato = anagrafica_privato.idanagrafica
                    
            else:
                return "Formato idanagrafica non valido."
        else:
            idanagrafica = None


        idcontenzioso=contenzioso.idcontenzioso
        
        
        contenziosi_with_idanagrafica.append((contenzioso, tp_nome, tp_cognome, tp_ragsociale, idanagrafica))


    return render_template('riepilogo_avvocato_ente.html',anagrafica_esistente=anagrafica_esistente, tp_nome=tp_nome, tp_cognome=tp_cognome,  contenziosi=contenziosi_with_idanagrafica,
                            user=utente)

@app.route('/riepilogo_utente_minerva', methods=['GET'])
def riepilogo_utente_minerva():

    utente = session.get('user_name')
    
    retrieved_idanagrafica = utente


    anagrafica_esistente = Contenzioso.query.filter(
    or_(
        Contenzioso.creato == retrieved_idanagrafica,
        Contenzioso.creato == 'Minerva',
        Contenzioso.modificato == retrieved_idanagrafica,
        Contenzioso.modificato == 'Minerva'
    )
    ).first()
    
    if anagrafica_esistente:
        tp_nome = session.get('user_name')
        tp_cognome = ""
        tp_email = session.get('user_email')
        tp_nomeutente = session.get('user_preferred_username','Impossibile ottenere.')
        tp_pec = ""
        tp_telefono = ""
        tp_codicefiscale = ""
        tp_idanagrafica = ""
        
        associazioni = Contenzioso.query.filter(
        or_(
            Contenzioso.creato == retrieved_idanagrafica,
            Contenzioso.creato == 'Minerva',
            Contenzioso.modificato == retrieved_idanagrafica,
            Contenzioso.modificato == 'Minerva'
        )
        ).all()
        

        contenziosi = []
        for associazione in associazioni:
            contenzioso = Contenzioso.query.filter_by(idcontenzioso=associazione.idcontenzioso).first()
            if contenzioso:
                contenziosi.append(contenzioso)

        return render_template('riepilogo_utente_minerva.html',user=utente , tp_nomeutente=tp_nomeutente ,contenziosi=contenziosi, tp_idanagrafica = tp_idanagrafica,tp_nome=tp_nome, tp_cognome=tp_cognome, tp_email=tp_email, tp_pec=tp_pec, tp_telefono=tp_telefono, tp_codicefiscale=tp_codicefiscale)

    else:
        return "Ops! Si è verificato un problema nell'apertura della tua scheda di riepilogo."

@app.route('/modifica_assegnazione_avvocato_ente', methods=['GET', 'POST'])
def modifica_assegnazione_avvocato_ente():


    utente = session.get('user_name')
    
    idcontenzioso = request.args.get('idcontenzioso')

    contenzioso = Contenzioso.query.filter_by(idcontenzioso=idcontenzioso).first_or_404()

    if request.method == 'POST':
        nuovo_idavvocatoente = request.form['idavvocatoente']
        avvocatoente = request.form['nomecompletoavvocatoente']
        contenzioso.idavvocatoente = nuovo_idavvocatoente
        contenzioso.avvocatoente = avvocatoente
        db.session.commit()
        return redirect(url_for('contenzioso', idcontenzioso=idcontenzioso, user=utente,))

    return render_template('modifica_assegnazione_avvocato_ente.html', contenzioso=contenzioso, user=utente)


@app.route('/modifica_contenzioso', methods=['GET', 'POST'])
def modifica_contenzioso():


    utente = session.get('user_name')
    
    idcontenzioso = request.args.get('idcontenzioso')


    if request.method == 'POST':
        numeroprotocollo = request.form['numeroprotocollo']
        dataprotocollo = request.form['dataprotocollo']
        tipologia = request.form['tipologia']
        annotributouno = request.form['annotributouno']
        annotributodue = request.form['annotributodue']
        annopresentazione = request.form['annopresentazione']
        autoritagiudiziaria = request.form['autoritagiudiziaria']
        numerorg = request.form['numerorg']
        if not numerorg:
            numerorg = ""
        dataudienza_str = request.form['dataudienza']   

        formato_input = '%Y-%m-%dT%H:%M'
        
        modificato=utente
        datamodifica=datetime.now().strftime('%d/%m/%Y %H:%M')
        operazioneeffettuata="Modifica del contenzioso."
        
        dataudienza = datetime.strptime(dataudienza_str, formato_input)
        print("Data e ora:", dataudienza)
        preavvisoudienza = dataudienza - timedelta(days=22)
        
        dataudienza = dataudienza.replace(hour=0, minute=0, second=0)
        sentenza = request.form['sentenza']   
        oggetto = request.form['oggetto']   
        valore = request.form['valore']
        note = request.form['note']

        contenzioso = Contenzioso.query.filter_by(idcontenzioso=idcontenzioso).first()
        calendario = Calendario.query.filter_by(idcontenzioso=idcontenzioso).first()
        if contenzioso:
            contenzioso.numeroprotocollo = numeroprotocollo
            contenzioso.dataprotocollo = dataprotocollo
            contenzioso.tipologia = tipologia
            contenzioso.annotributouno = annotributouno
            contenzioso.annotributodue = annotributodue
            contenzioso.annopresentazione = annopresentazione
            contenzioso.autoritagiudiziaria = autoritagiudiziaria
            contenzioso.numerorg = numerorg
            calendario.data = dataudienza
            calendario.preavviso = preavvisoudienza
            contenzioso.sentenza = sentenza
            contenzioso.oggetto = oggetto
            contenzioso.valore = valore
            contenzioso.note = note
            contenzioso.modificato = modificato
            contenzioso.datamodifica = datamodifica
            contenzioso.operazioneeffettuata = operazioneeffettuata

            db.session.commit()

            return redirect(url_for('contenzioso', idcontenzioso=idcontenzioso))

    existing_data = Contenzioso.query.filter_by(idcontenzioso=idcontenzioso).first()
    existing_data_calendario = Calendario.query.filter_by(idcontenzioso=idcontenzioso).first()
    print(existing_data_calendario)
    return render_template('modifica_contenzioso.html', idcontenzioso=idcontenzioso, existing_data=existing_data, existing_data_calendario=existing_data_calendario,user=utente)

@app.route('/contenzioso', methods=['GET'])
def contenzioso():

    utente = session.get('user_name')
    

    idcontenzioso = request.args.get('idcontenzioso')

    contenzioso = Contenzioso.query.filter_by(idcontenzioso=idcontenzioso).first()
    associazione = Associazioni.query.filter_by(idcontenzioso=idcontenzioso).first()
    calendario = Calendario.query.filter_by(idcontenzioso=idcontenzioso).first()
    
    idlegale = associazione.idlegale
    idlegaledue = associazione.idlegaledue
    
    legale = Legale.query.filter_by(idlegale=idlegale).first()
    legaledue = Legale.query.filter_by(idlegale=idlegaledue).first()
    
    tp_nome_legale = legale.nome
    tp_cognome_legale = legale.cognome
    tp_telefono_legale = legale.telefono
    tp_email_legale = legale.email
    tp_pec_legale = legale.pec
    tp_idlegale = legale.idlegale
    
   
    tp_numeroprotocollo = contenzioso.numeroprotocollo
    tp_dataprotocollo = contenzioso.dataprotocollo
    tp_tipologia = contenzioso.tipologia
    tp_annotributouno = contenzioso.annotributouno
    tp_annotributodue = contenzioso.annotributodue
    tp_annopresentazione = contenzioso.annopresentazione
    tp_avvocatoente = contenzioso.avvocatoente
    tp_autoritagiudiziaria = contenzioso.autoritagiudiziaria
    tp_numerorg = contenzioso.numerorg
    tp_dataudienza = calendario.data
    tp_sentenza = contenzioso.sentenza  
    tp_oggetto = contenzioso.oggetto
    tp_valore = contenzioso.valore
    tp_note = contenzioso.note
    tp_creato = contenzioso.creato
    tp_modificato = contenzioso.modificato
    tp_datainserimento = contenzioso.datainserimento
    tp_datamodifica = contenzioso.datamodifica
    tp_operazioneeffettuata = contenzioso.operazioneeffettuata
    
    
        
    if ' ' not in tp_dataudienza:
        tp_dataudienza += ' 00:00:00' 

    try:
        tp_dataudienza = datetime.strptime(tp_dataudienza, '%Y-%m-%d %H:%M:%S').date()
    except ValueError:
        print("Error parsing datetime")

    
    if contenzioso:
        associazioni = Associazioni.query.filter_by(idcontenzioso=idcontenzioso).first()
        idanagrafica = associazioni.idanagrafica

        if idanagrafica.startswith("AZ"):
            anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
            if anagrafica_azienda:
                tp_ragsociale = anagrafica_azienda.ragsociale
                tp_email = anagrafica_azienda.email
                tp_pec = anagrafica_azienda.pec
                tp_telefono = anagrafica_azienda.telefono
                tp_piva = anagrafica_azienda.piva
                tp_idanagraficaazienda = anagrafica_azienda.idanagrafica


        elif idanagrafica.startswith("PP"):
            anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
            if anagrafica_privato:
                tp_nome = anagrafica_privato.nome
                tp_cognome = anagrafica_privato.cognome
                tp_email = anagrafica_privato.email
                tp_pec = anagrafica_privato.pec
                tp_telefono = anagrafica_privato.telefono
                tp_codicefiscale = anagrafica_privato.codicefiscale
                tp_idanagraficaprivato = anagrafica_privato.idanagrafica

        else:
            return "Formato idanagrafica non valido."

        
        folder_path = os.path.join("archivio", idcontenzioso)
        if os.path.exists(folder_path):
            file_list = os.listdir(folder_path)
        else:
            file_list = []
        
        print(datetime.now().strftime('%Y/%m/%d %H:%M:%S'),"E' stato visualizzato un contenzioso")
        return render_template('contenzioso.html', idcontenzioso=idcontenzioso,
                               tp_ragsociale=tp_ragsociale if idanagrafica.startswith("AZ") else "",
                               tp_idanagrafica=tp_idanagraficaazienda if idanagrafica.startswith("AZ") else tp_idanagraficaprivato,
                               tp_nome=tp_nome if idanagrafica.startswith("PP") else "",
                               tp_cognome=tp_cognome if idanagrafica.startswith("PP") else "",
                               tp_email=tp_email if idanagrafica.startswith("PP") else tp_email,
                               tp_pec=tp_pec if idanagrafica.startswith("PP") else tp_pec,
                               tp_telefono=tp_telefono if idanagrafica.startswith("PP") else tp_pec,
                               tp_codicefiscale=tp_codicefiscale if idanagrafica.startswith("PP") else tp_piva,
                               tp_nome_legale=tp_nome_legale, tp_cognome_legale=tp_cognome_legale,
                               tp_email_legale=tp_email_legale, tp_pec_legale=tp_pec_legale, tp_telefono_legale=tp_telefono_legale,
                               tp_numeroprotocollo=tp_numeroprotocollo, tp_dataprotocollo=tp_dataprotocollo, tp_oggetto=tp_oggetto, 
                               tp_tipologia=tp_tipologia, tp_annotributouno=tp_annotributouno, tp_annotributodue=tp_annotributodue,
                               tp_annopresentazione=tp_annopresentazione, tp_valore=tp_valore, tp_avvocatoente=tp_avvocatoente,
                               tp_autoritagiudiziaria=tp_autoritagiudiziaria, tp_numerorg=tp_numerorg, tp_dataudienza=tp_dataudienza,
                               tp_sentenza=tp_sentenza, tp_note=tp_note, tp_idlegale=tp_idlegale, 
                               file_list=file_list, legaledue=legaledue, user=utente,
                               tp_creato=tp_creato,tp_modificato=tp_modificato, tp_datainserimento=tp_datainserimento, tp_datamodifica=tp_datamodifica, tp_operazioneeffettuata=tp_operazioneeffettuata

        )

    else:
        return "Contenzioso non trovato."

@app.route('/upload_file', methods=['POST'])
def upload_file():


    utente = session.get('user_name')
    
    idcontenzioso = request.form.get('idcontenzioso')

    folder_path = os.path.abspath(os.path.join("archivio", idcontenzioso))
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    uploaded_files = request.files.getlist('files') 
    
    contenzioso = Contenzioso.query.filter_by(idcontenzioso=idcontenzioso).first()
    modificato=session.get("user", {}).get("userinfo", {}).get("name")
    datamodifica=datetime.now().strftime('%d/%m/%Y %H:%M')
    operazioneeffettuata="Caricamento di file."
    
    for uploaded_file in uploaded_files:
        if uploaded_file:
            base, ext = os.path.splitext(uploaded_file.filename)
            file_path = os.path.join(folder_path, uploaded_file.filename)

            count = 1
            while os.path.exists(file_path):
                new_filename = f"{base}-{count}{ext}"
                file_path = os.path.join(folder_path, new_filename)
                count += 1

            print(f"Saving file to: {file_path}")
            uploaded_file.save(file_path)

            if file_path.endswith('.zip'):
                print(f"Extracting ZIP file: {file_path}")
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(folder_path)
                os.remove(file_path)  
                
            if contenzioso:
                contenzioso.modificato = modificato
                contenzioso.datamodifica = datamodifica
                contenzioso.operazioneeffettuata = operazioneeffettuata

                db.session.commit()

    return redirect(url_for('contenzioso', idcontenzioso=idcontenzioso, user=utente))

@app.route('/visualizza_file', methods=['GET'])
def visualizza_file():

    utente = session.get('user_name')
    
    idcontenzioso = request.args.get('idcontenzioso')
    file_name = request.args.get('file_name')

    folder_path = os.path.join("archivio", idcontenzioso)
    file_path = os.path.join(folder_path, file_name)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=False)

    return "File non trovato."

@app.route('/scarica_file', methods=['GET'])
def scarica_file():


    utente = session.get('user_name')
    
    idcontenzioso = request.args.get('idcontenzioso')
    file_name = request.args.get('file_name')

    folder_path = os.path.join("archivio", idcontenzioso)
    file_path = os.path.join(folder_path, file_name)

    if os.path.exists(file_path):
        return send_from_directory(folder_path, file_name, as_attachment=True)

    return "File non trovato."


@app.route('/cancella_file', methods=['GET'])
def cancella_file():


    utente = session.get('user_name')
    
    idcontenzioso = request.args.get('idcontenzioso')
    file_name = request.args.get('file_name')
    
    folder_path = os.path.join("archivio", idcontenzioso)
    file_path = os.path.join(folder_path, file_name)

    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect(url_for('contenzioso', idcontenzioso=idcontenzioso, user=utente))

    return "File non trovato."

@app.route('/scarica_tutti_i_file', methods=['GET'])
def scarica_tutti_i_file():

    utente = session.get('user_name')
    
    idcontenzioso = request.args.get('idcontenzioso')

    folder_path = os.path.join("archivio", idcontenzioso)
    
    if os.path.exists(folder_path):
        zip_filename = os.path.join("archivio", idcontenzioso + "_Export.zip")
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, folder_path))

        return send_from_directory('archivio', idcontenzioso + '_Export.zip', as_attachment=True)

    return "Cartella non trovata."

@app.route('/salva_modifiche', methods=['POST'])
def salva_modifiche():

    utente = session.get('user_name')
    

    idcontenzioso = request.form.get('idcontenzioso')
    
    numeroprotocollo = request.form.get('numeroprotocollo')
    dataprotocollo = request.form.get('dataprotocollo')
    tipologia = request.form.get('tipologia')
    annotributouno = request.form.get('annotributouno')
    annotributodue = request.form.get('annotributodue')
    annopresentazione = request.form.get('annopresentazione')
    autoritagiudiziaria = request.form.get('autoritagiudiziaria')
    numerorg = request.form.get('numerorg')
    if not numerorg:
        numerorg = ""
    dataudienza = request.form.get('dataudienza')
    sentenza = request.form.get('sentenza')
    oggetto = request.form.get('oggetto')   
    valore = request.form.get('valore')
    note = request.form.get('note')
    modificato=session.get("user", {}).get("userinfo", {}).get("name")
    datamodifica=datetime.now().strftime('%d/%m/%Y %H:%M')
    operazioneeffettuata="Modifica del contenzioso."

    contenzioso = Contenzioso.query.filter_by(idcontenzioso=idcontenzioso).first()
    calendario = Calendario.query.filter_by(idcontenzioso=idcontenzioso).first()
    if contenzioso:
        contenzioso.numeroprotocollo = numeroprotocollo
        contenzioso.dataprotocollo = dataprotocollo
        contenzioso.tipologia = tipologia
        contenzioso.annotributouno = annotributouno
        contenzioso.annotributodue = annotributodue
        contenzioso.annopresentazione = annopresentazione
        contenzioso.autoritagiudiziaria = autoritagiudiziaria
        contenzioso.numerorg = numerorg
        calendario.data = dataudienza
        contenzioso.sentenza = sentenza
        contenzioso.oggetto = oggetto
        contenzioso.valore = valore
        contenzioso.note = note
        contenzioso.modificato = modificato
        contenzioso.datamodifica = datamodifica
        contenzioso.operazioneeffettuata = operazioneeffettuata
        
    try:
        db.session.commit()
    except Exception as e:
        print(f"Errore durante il commit nel database: {str(e)}")
        db.session.rollback()  


        return jsonify({'message': 'Modifiche salvate con successo'})
    else:
        return jsonify({'message': 'Contenzioso non trovato'}, 400)

@app.route('/ricerca_protocollo', methods=['GET', 'POST'])
def ricerca_protocollo():

    utente = session.get('user_name')
    
    if request.method == 'POST':
        numeroprotocollo = request.form['numeroprotocollo']
        dataprotocollo = request.form['dataprotocollo']
        if not numeroprotocollo or not dataprotocollo:
            return "È necessario inserire dei valori per poter effettuare la ricerca." 
        else:
            contenzioso = Contenzioso.query.filter_by(numeroprotocollo=numeroprotocollo, dataprotocollo=dataprotocollo).first()
            if contenzioso:
                idcontenzioso = contenzioso.idcontenzioso
                print(datetime.now().strftime('%Y/%m/%d %H:%M:%S'),"Ricerca effettuata tramite numero di protocollo")
                return redirect(url_for('contenzioso', idcontenzioso=idcontenzioso, user=utente))
            else:
                return "Non è stato possibile trovare una corrispondenza nel database per questa combinazione di Numero e Data di protocollo. Forse il ricorso non è stato aggiunto o i dati immessi sono errati?"  
    return render_template('ricerca_protocollo.html',user=utente)

@app.route('/ricerca_contenzioso', methods=['GET', 'POST'])
def ricerca_contenzioso():

    utente = session.get('user_name')
    
    if request.method == 'POST':
        numerocontenzioso = request.form['numerocontenzioso']
        if not numerocontenzioso:
            return "È necessario inserire dei valori per poter effettuare la ricerca." 
        else:
            contenzioso = Contenzioso.query.filter_by(idcontenzioso=numerocontenzioso).first()
            if contenzioso:
                idcontenzioso = contenzioso.idcontenzioso
                print(datetime.now().strftime('%Y/%m/%d %H:%M:%S'),"Ricerca effettuata tramite ID contenzioso")
                return redirect(url_for('contenzioso', idcontenzioso=idcontenzioso,user=utente))
            else:
                return "Non è stato possibile trovare una corrispondenza nel database per questa combinazione di Numero e Data di protocollo. Forse il ricorso non è stato aggiunto o i dati immessi sono errati?"  
    return render_template('ricerca_contenzioso.html',user=utente)

@app.route('/riepilogo_contenziosi_rg', methods=['GET'])
def riepilogo_contenziosi_rg():

    utente = session.get('user_name')
    

    contenziosi_with_idanagrafica = []
    anno = None
    tipologia = None

    contenziosi = Contenzioso.query.filter((Contenzioso.numerorg != "")).all()
    print(contenziosi)
    for contenzioso in contenziosi:
        idcontenzioso = contenzioso.idcontenzioso
        associazione = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
        retrieve_idanagrafica = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
        if associazione:
            idanagrafica = retrieve_idanagrafica.idanagrafica
            if idanagrafica.startswith("AZ"):
                anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_azienda:
                    tp_nome=""
                    tp_cognome=""
                    tp_codicefiscale=""
                    tp_ragsociale = anagrafica_azienda.ragsociale
                    print("TrovataRAGSOCIALE",tp_ragsociale)
                    tp_email = anagrafica_azienda.email
                    tp_pec = anagrafica_azienda.pec
                    tp_telefono = anagrafica_azienda.telefono
                    tp_piva = anagrafica_azienda.piva
                    tp_idanagraficaazienda = anagrafica_azienda.idanagrafica
            elif idanagrafica.startswith("PP"):
                anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_privato:
                    tp_ragsociale=""
                    tp_piva=""
                    tp_nome = anagrafica_privato.nome
                    tp_cognome = anagrafica_privato.cognome
                    tp_email = anagrafica_privato.email
                    tp_pec = anagrafica_privato.pec
                    tp_telefono = anagrafica_privato.telefono
                    tp_codicefiscale = anagrafica_privato.codicefiscale
                    tp_idanagraficaprivato = anagrafica_privato.idanagrafica
            else:
                return "Formato idanagrafica non valido."
            
                associazione = Associazioni.query.filter_by(idcontenzioso=idcontenzioso).first()

            idlegale = associazione.idlegale
            idlegaledue = associazione.idlegaledue
            
            legale = Legale.query.filter_by(idlegale=idlegale).first()
            legaledue = Legale.query.filter_by(idlegale=idlegaledue).first()
            
            tp_nome_legale = legale.nome
            tp_cognome_legale = legale.cognome
            tp_telefono_legale = legale.telefono
            tp_email_legale = legale.email
            tp_pec_legale = legale.pec
            tp_idlegale = legale.idlegale
            
            if legaledue is not None:
                tp_nome_legale_due = legaledue.nome
                tp_cognome_legale_due = legaledue.cognome
                tp_telefono_legale_due = legaledue.telefono
                tp_email_legale_due = legaledue.email
                tp_pec_legale_due = legaledue.pec
                tp_idlegale_due = legaledue.idlegale
            else:
                tp_nome_legale_due = ""
                tp_cognome_legale_due = ""
                tp_telefono_legale_due = ""
                tp_email_legale_due = ""
                tp_pec_legale_due = ""
                tp_idlegale_due = ""
                
            
        else:
            idanagrafica = None

        idcontenzioso=contenzioso.idcontenzioso
        
        calendario = Calendario.query.filter_by(idcontenzioso=contenzioso.idcontenzioso).first()
        tp_dataudienza=None
        tp_dataudienza=calendario.data
        tp_preavvisoudienza=calendario.preavviso
        
        contenziosi_with_idanagrafica.append((contenzioso, tp_nome, tp_cognome, tp_ragsociale, idanagrafica))
        print("cc_",contenziosi_with_idanagrafica)
        print("cc_",tp_ragsociale)

    return render_template('riepilogo_contenziosi_rg.html', tipologia=tipologia, contenziosi=contenziosi_with_idanagrafica,
                            user=utente)

@app.route('/riepilogo_contenziosi_senza_rg', methods=['GET'])
def riepilogo_contenziosi_senza_rg():

    utente = session.get('user_name')
    
    contenziosi_with_idanagrafica = []
    anno = None
    tipologia = None

    contenziosi = Contenzioso.query.filter((Contenzioso.numerorg == "")).all()
    print(contenziosi)
    for contenzioso in contenziosi:
        idcontenzioso = contenzioso.idcontenzioso
        associazione = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
        retrieve_idanagrafica = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
        if associazione:
            idanagrafica = retrieve_idanagrafica.idanagrafica
            if idanagrafica.startswith("AZ"):
                anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_azienda:
                    tp_nome=""
                    tp_cognome=""
                    tp_codicefiscale=""
                    tp_ragsociale = anagrafica_azienda.ragsociale
                    print("TrovataRAGSOCIALE",tp_ragsociale)
                    tp_email = anagrafica_azienda.email
                    tp_pec = anagrafica_azienda.pec
                    tp_telefono = anagrafica_azienda.telefono
                    tp_piva = anagrafica_azienda.piva
                    tp_idanagraficaazienda = anagrafica_azienda.idanagrafica
            elif idanagrafica.startswith("PP"):
                anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_privato:
                    tp_ragsociale=""
                    tp_piva=""
                    tp_nome = anagrafica_privato.nome
                    tp_cognome = anagrafica_privato.cognome
                    tp_email = anagrafica_privato.email
                    tp_pec = anagrafica_privato.pec
                    tp_telefono = anagrafica_privato.telefono
                    tp_codicefiscale = anagrafica_privato.codicefiscale
                    tp_idanagraficaprivato = anagrafica_privato.idanagrafica
            else:
                return "Formato idanagrafica non valido."
            
                associazione = Associazioni.query.filter_by(idcontenzioso=idcontenzioso).first()

            idlegale = associazione.idlegale
            idlegaledue = associazione.idlegaledue
            
            legale = Legale.query.filter_by(idlegale=idlegale).first()
            legaledue = Legale.query.filter_by(idlegale=idlegaledue).first()
            
            tp_nome_legale = legale.nome
            tp_cognome_legale = legale.cognome
            tp_telefono_legale = legale.telefono
            tp_email_legale = legale.email
            tp_pec_legale = legale.pec
            tp_idlegale = legale.idlegale
            
            if legaledue is not None:
                tp_nome_legale_due = legaledue.nome
                tp_cognome_legale_due = legaledue.cognome
                tp_telefono_legale_due = legaledue.telefono
                tp_email_legale_due = legaledue.email
                tp_pec_legale_due = legaledue.pec
                tp_idlegale_due = legaledue.idlegale
            else:
                tp_nome_legale_due = ""
                tp_cognome_legale_due = ""
                tp_telefono_legale_due = ""
                tp_email_legale_due = ""
                tp_pec_legale_due = ""
                tp_idlegale_due = ""
                
            
        else:
            idanagrafica = None

        idcontenzioso=contenzioso.idcontenzioso
        
        calendario = Calendario.query.filter_by(idcontenzioso=contenzioso.idcontenzioso).first()
        tp_dataudienza=None
        tp_dataudienza=calendario.data
        tp_preavvisoudienza=calendario.preavviso
        
        contenziosi_with_idanagrafica.append((contenzioso, tp_nome, tp_cognome, tp_ragsociale, idanagrafica))
        print("cc_",contenziosi_with_idanagrafica)
        print("cc_",tp_ragsociale)

    return render_template('riepilogo_contenziosi_senza_rg.html', tipologia=tipologia, contenziosi=contenziosi_with_idanagrafica,
                            user=utente)

@app.route('/riepilogo_contenziosi_anno/presentazione', methods=['GET', 'POST'])
def riepilogo_contenziosi_anno_presentazione():

    utente = session.get('user_name')
    
    contenziosi_with_idanagrafica = []
    anno = None

    contenzioso_annotributo = []  
    anno = None


    if request.method == 'POST':
        anno = request.form['anno']
        anno_int = int(anno)
        if not anno_int or anno_int < 2000 or anno_int > 2099:
            return "Il valore inserito non è valido. Un valore valido contiene un anno compreso tra 2000 e 2099"
        elif anno_int is None:
            return redirect(url_for("index"))
        else:
                contenziosi = Contenzioso.query.filter(Contenzioso.annopresentazione == anno_int).all()
        for contenzioso in contenziosi:
            idcontenzioso = contenzioso.idcontenzioso
            associazione = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
            retrieve_idanagrafica = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
            if associazione:
                idanagrafica = retrieve_idanagrafica.idanagrafica
                if idanagrafica.startswith("AZ"):
                    anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                    if anagrafica_azienda:
                        tp_nome=""
                        tp_cognome=""
                        tp_codicefiscale=""
                        tp_ragsociale = anagrafica_azienda.ragsociale
                        print("TrovataRAGSOCIALE",tp_ragsociale)
                        tp_email = anagrafica_azienda.email
                        tp_pec = anagrafica_azienda.pec
                        tp_telefono = anagrafica_azienda.telefono
                        tp_piva = anagrafica_azienda.piva
                        tp_idanagraficaazienda = anagrafica_azienda.idanagrafica
                elif idanagrafica.startswith("PP"):
                    anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                    if anagrafica_privato:
                        tp_ragsociale=""
                        tp_piva=""
                        tp_nome = anagrafica_privato.nome
                        tp_cognome = anagrafica_privato.cognome
                        tp_email = anagrafica_privato.email
                        tp_pec = anagrafica_privato.pec
                        tp_telefono = anagrafica_privato.telefono
                        tp_codicefiscale = anagrafica_privato.codicefiscale
                        tp_idanagraficaprivato = anagrafica_privato.idanagrafica
                else:
                    return "Formato idanagrafica non valido."
                
                    associazione = Associazioni.query.filter_by(idcontenzioso=idcontenzioso).first()

                idlegale = associazione.idlegale
                idlegaledue = associazione.idlegaledue
                
                legale = Legale.query.filter_by(idlegale=idlegale).first()
                legaledue = Legale.query.filter_by(idlegale=idlegaledue).first()
                
                tp_nome_legale = legale.nome
                tp_cognome_legale = legale.cognome
                tp_telefono_legale = legale.telefono
                tp_email_legale = legale.email
                tp_pec_legale = legale.pec
                tp_idlegale = legale.idlegale
                
                if legaledue is not None:
                    tp_nome_legale_due = legaledue.nome
                    tp_cognome_legale_due = legaledue.cognome
                    tp_telefono_legale_due = legaledue.telefono
                    tp_email_legale_due = legaledue.email
                    tp_pec_legale_due = legaledue.pec
                    tp_idlegale_due = legaledue.idlegale
                else:
                    tp_nome_legale_due = ""
                    tp_cognome_legale_due = ""
                    tp_telefono_legale_due = ""
                    tp_email_legale_due = ""
                    tp_pec_legale_due = ""
                    tp_idlegale_due = ""
                    
                
            else:
                idanagrafica = None

            idcontenzioso=contenzioso.idcontenzioso
            
            calendario = Calendario.query.filter_by(idcontenzioso=contenzioso.idcontenzioso).first()
            tp_dataudienza=None
            tp_dataudienza=calendario.data
            tp_preavvisoudienza=calendario.preavviso
            
            contenziosi_with_idanagrafica.append((contenzioso, anno , tp_nome, tp_cognome, tp_ragsociale, idanagrafica))

    
    return render_template('riepilogo_contenziosi_anno_presentazione.html', anno=anno, contenziosi=contenziosi_with_idanagrafica,
                            user=utente)

@app.route('/riepilogo_contenziosi_anno/tributo', methods=['GET', 'POST'])
def riepilogo_contenziosi_anno_tributo():

    utente = session.get('user_name')
    
    contenziosi_with_idanagrafica = []
    contenzioso_annotributo = []  
    anno = None


    if request.method == 'POST':
        anno = request.form['anno']
        anno_int = int(anno)
        if not anno_int or anno_int < 2000 or anno_int > 2099:
            return "Il valore inserito non è valido. Un valore valido contiene un anno compreso tra 2000 e 2099"
        elif anno_int is None:
            return redirect(url_for("index"))
        else:
                contenziosi = Contenzioso.query.filter(
                    and_(Contenzioso.annotributouno <= anno_int, Contenzioso.annotributodue >= anno_int)).all()
        for contenzioso in contenziosi:
            idcontenzioso = contenzioso.idcontenzioso
            associazione = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
            retrieve_idanagrafica = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
            if associazione:
                idanagrafica = retrieve_idanagrafica.idanagrafica
                if idanagrafica.startswith("AZ"):
                    anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                    if anagrafica_azienda:
                        tp_nome=""
                        tp_cognome=""
                        tp_codicefiscale=""
                        tp_ragsociale = anagrafica_azienda.ragsociale
                        print("TrovataRAGSOCIALE",tp_ragsociale)
                        tp_email = anagrafica_azienda.email
                        tp_pec = anagrafica_azienda.pec
                        tp_telefono = anagrafica_azienda.telefono
                        tp_piva = anagrafica_azienda.piva
                        tp_idanagraficaazienda = anagrafica_azienda.idanagrafica
                elif idanagrafica.startswith("PP"):
                    anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                    if anagrafica_privato:
                        tp_ragsociale=""
                        tp_piva=""
                        tp_nome = anagrafica_privato.nome
                        tp_cognome = anagrafica_privato.cognome
                        tp_email = anagrafica_privato.email
                        tp_pec = anagrafica_privato.pec
                        tp_telefono = anagrafica_privato.telefono
                        tp_codicefiscale = anagrafica_privato.codicefiscale
                        tp_idanagraficaprivato = anagrafica_privato.idanagrafica
                else:
                    return "Formato idanagrafica non valido."
                
                    associazione = Associazioni.query.filter_by(idcontenzioso=idcontenzioso).first()

                idlegale = associazione.idlegale
                idlegaledue = associazione.idlegaledue
                
                legale = Legale.query.filter_by(idlegale=idlegale).first()
                legaledue = Legale.query.filter_by(idlegale=idlegaledue).first()
                
                tp_nome_legale = legale.nome
                tp_cognome_legale = legale.cognome
                tp_telefono_legale = legale.telefono
                tp_email_legale = legale.email
                tp_pec_legale = legale.pec
                tp_idlegale = legale.idlegale
                
                if legaledue is not None:
                    tp_nome_legale_due = legaledue.nome
                    tp_cognome_legale_due = legaledue.cognome
                    tp_telefono_legale_due = legaledue.telefono
                    tp_email_legale_due = legaledue.email
                    tp_pec_legale_due = legaledue.pec
                    tp_idlegale_due = legaledue.idlegale
                else:
                    tp_nome_legale_due = ""
                    tp_cognome_legale_due = ""
                    tp_telefono_legale_due = ""
                    tp_email_legale_due = ""
                    tp_pec_legale_due = ""
                    tp_idlegale_due = ""
                    
                
            else:
                idanagrafica = None

            

            idcontenzioso=contenzioso.idcontenzioso
            
            calendario = Calendario.query.filter_by(idcontenzioso=contenzioso.idcontenzioso).first()
            tp_dataudienza=None
            tp_dataudienza=calendario.data
            tp_preavvisoudienza=calendario.preavviso
            
            contenziosi_with_idanagrafica.append((contenzioso, anno , tp_nome, tp_cognome, tp_ragsociale, idanagrafica))
            print("cc_",tp_ragsociale)
       
    return render_template('riepilogo_contenziosi_anno_tributo.html', anno=anno, contenziosi=contenziosi_with_idanagrafica,
                            user=utente)

@app.route('/riepilogo_contenziosi_tipologia', methods=['GET', 'POST'])
def riepilogo_contenziosi_tipologia():

    utente = session.get('user_name')
    
    contenziosi_with_idanagrafica = []
    anno = None
    tipologia = None

    if request.method == 'POST':
        tipologia = request.form['tipologia']
        contenziosi = Contenzioso.query.filter(Contenzioso.tipologia == tipologia).all()
        for contenzioso in contenziosi:
            idcontenzioso = contenzioso.idcontenzioso
            associazione = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
            retrieve_idanagrafica = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
            if associazione:
                idanagrafica = retrieve_idanagrafica.idanagrafica
                if idanagrafica.startswith("AZ"):
                    anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                    if anagrafica_azienda:
                        tp_nome=""
                        tp_cognome=""
                        tp_codicefiscale=""
                        tp_ragsociale = anagrafica_azienda.ragsociale
                        print("TrovataRAGSOCIALE",tp_ragsociale)
                        tp_email = anagrafica_azienda.email
                        tp_pec = anagrafica_azienda.pec
                        tp_telefono = anagrafica_azienda.telefono
                        tp_piva = anagrafica_azienda.piva
                        tp_idanagraficaazienda = anagrafica_azienda.idanagrafica
                elif idanagrafica.startswith("PP"):
                    anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                    if anagrafica_privato:
                        tp_ragsociale=""
                        tp_piva=""
                        tp_nome = anagrafica_privato.nome
                        tp_cognome = anagrafica_privato.cognome
                        tp_email = anagrafica_privato.email
                        tp_pec = anagrafica_privato.pec
                        tp_telefono = anagrafica_privato.telefono
                        tp_codicefiscale = anagrafica_privato.codicefiscale
                        tp_idanagraficaprivato = anagrafica_privato.idanagrafica
                else:
                    return "Formato idanagrafica non valido."
                
                    associazione = Associazioni.query.filter_by(idcontenzioso=idcontenzioso).first()

                idlegale = associazione.idlegale
                idlegaledue = associazione.idlegaledue
                
                legale = Legale.query.filter_by(idlegale=idlegale).first()
                legaledue = Legale.query.filter_by(idlegale=idlegaledue).first()
                
                tp_nome_legale = legale.nome
                tp_cognome_legale = legale.cognome
                tp_telefono_legale = legale.telefono
                tp_email_legale = legale.email
                tp_pec_legale = legale.pec
                tp_idlegale = legale.idlegale
                
                if legaledue is not None:
                    tp_nome_legale_due = legaledue.nome
                    tp_cognome_legale_due = legaledue.cognome
                    tp_telefono_legale_due = legaledue.telefono
                    tp_email_legale_due = legaledue.email
                    tp_pec_legale_due = legaledue.pec
                    tp_idlegale_due = legaledue.idlegale
                else:
                    tp_nome_legale_due = ""
                    tp_cognome_legale_due = ""
                    tp_telefono_legale_due = ""
                    tp_email_legale_due = ""
                    tp_pec_legale_due = ""
                    tp_idlegale_due = ""
                    
                
            else:
                idanagrafica = None

            idcontenzioso=contenzioso.idcontenzioso
            
            calendario = Calendario.query.filter_by(idcontenzioso=contenzioso.idcontenzioso).first()
            tp_dataudienza=None
            tp_dataudienza=calendario.data
            tp_preavvisoudienza=calendario.preavviso
            
            contenziosi_with_idanagrafica.append((contenzioso, tipologia , tp_nome, tp_cognome, tp_ragsociale, idanagrafica))
            print("cc_",contenziosi_with_idanagrafica)
            print("cc_",tp_ragsociale)

    return render_template('riepilogo_contenziosi_tipologia.html', tipologia=tipologia, contenziosi=contenziosi_with_idanagrafica,
                            user=utente)

@app.route('/riepilogo_contenziosi_autorita_giudiziaria', methods=['GET', 'POST'])
def riepilogo_contenziosi_autorita_giudiziaria():

    utente = session.get('user_name')
    
    contenziosi_with_idanagrafica = []
    anno = None
    autoritagiudiziaria = None

    if request.method == 'POST':
        autoritagiudiziaria = request.form['autoritagiudiziaria']
        contenziosi = Contenzioso.query.filter(Contenzioso.autoritagiudiziaria == autoritagiudiziaria).all()
        for contenzioso in contenziosi:
            idcontenzioso = contenzioso.idcontenzioso
            associazione = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
            retrieve_idanagrafica = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()
            if associazione:
                idanagrafica = retrieve_idanagrafica.idanagrafica
                if idanagrafica.startswith("AZ"):
                    anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                    if anagrafica_azienda:
                        tp_nome=""
                        tp_cognome=""
                        tp_codicefiscale=""
                        tp_ragsociale = anagrafica_azienda.ragsociale
                        print("TrovataRAGSOCIALE",tp_ragsociale)
                        tp_email = anagrafica_azienda.email
                        tp_pec = anagrafica_azienda.pec
                        tp_telefono = anagrafica_azienda.telefono
                        tp_piva = anagrafica_azienda.piva
                        tp_idanagraficaazienda = anagrafica_azienda.idanagrafica
                elif idanagrafica.startswith("PP"):
                    anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                    if anagrafica_privato:
                        tp_ragsociale=""
                        tp_piva=""
                        tp_nome = anagrafica_privato.nome
                        tp_cognome = anagrafica_privato.cognome
                        tp_email = anagrafica_privato.email
                        tp_pec = anagrafica_privato.pec
                        tp_telefono = anagrafica_privato.telefono
                        tp_codicefiscale = anagrafica_privato.codicefiscale
                        tp_idanagraficaprivato = anagrafica_privato.idanagrafica
                else:
                    return "Formato idanagrafica non valido."
                
                    associazione = Associazioni.query.filter_by(idcontenzioso=idcontenzioso).first()

                idlegale = associazione.idlegale
                idlegaledue = associazione.idlegaledue
                
                legale = Legale.query.filter_by(idlegale=idlegale).first()
                legaledue = Legale.query.filter_by(idlegale=idlegaledue).first()
                
                tp_nome_legale = legale.nome
                tp_cognome_legale = legale.cognome
                tp_telefono_legale = legale.telefono
                tp_email_legale = legale.email
                tp_pec_legale = legale.pec
                tp_idlegale = legale.idlegale
                
                if legaledue is not None:
                    tp_nome_legale_due = legaledue.nome
                    tp_cognome_legale_due = legaledue.cognome
                    tp_telefono_legale_due = legaledue.telefono
                    tp_email_legale_due = legaledue.email
                    tp_pec_legale_due = legaledue.pec
                    tp_idlegale_due = legaledue.idlegale
                else:
                    tp_nome_legale_due = ""
                    tp_cognome_legale_due = ""
                    tp_telefono_legale_due = ""
                    tp_email_legale_due = ""
                    tp_pec_legale_due = ""
                    tp_idlegale_due = ""
                    
                
            else:
                idanagrafica = None

            idcontenzioso=contenzioso.idcontenzioso
            
            calendario = Calendario.query.filter_by(idcontenzioso=contenzioso.idcontenzioso).first()
            tp_dataudienza=None
            tp_dataudienza=calendario.data
            tp_preavvisoudienza=calendario.preavviso
            
            contenziosi_with_idanagrafica.append((contenzioso, autoritagiudiziaria , tp_nome, tp_cognome, tp_ragsociale, idanagrafica))
            print("cc_",contenziosi_with_idanagrafica)
            print("cc_",tp_ragsociale)

    return render_template('riepilogo_contenziosi_autorita_giudiziaria.html', autoritagiudiziaria=autoritagiudiziaria, contenziosi=contenziosi_with_idanagrafica,
                            user=utente)


@app.route('/contenziosi')
def contenziosi():

    utente = session.get('user_name')
    
    contenziosi = db.session.query(Contenzioso).all()

    contenziosi_with_idanagrafica = []

    for contenzioso in contenziosi:
        idcontenzioso = contenzioso.idcontenzioso
        associazione = db.session.query(Associazioni).filter_by(idcontenzioso=idcontenzioso).first()

        if associazione:
            idanagrafica = associazione.idanagrafica
            if idanagrafica.startswith("AZ"):
                anagrafica_azienda = AnagraficaAzienda.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_azienda:
                    tp_nome=""
                    tp_cognome=""
                    tp_codicefiscale=""
                    tp_ragsociale = anagrafica_azienda.ragsociale
                    tp_email = anagrafica_azienda.email
                    tp_pec = anagrafica_azienda.pec
                    tp_telefono = anagrafica_azienda.telefono
                    tp_piva = anagrafica_azienda.piva
                    tp_idanagraficaazienda = anagrafica_azienda.idanagrafica
            elif idanagrafica.startswith("PP"):
                anagrafica_privato = AnagraficaPrivato.query.filter_by(idanagrafica=idanagrafica).first()
                if anagrafica_privato:
                    tp_ragsociale=""
                    tp_piva=""
                    tp_nome = anagrafica_privato.nome
                    tp_cognome = anagrafica_privato.cognome
                    tp_email = anagrafica_privato.email
                    tp_pec = anagrafica_privato.pec
                    tp_telefono = anagrafica_privato.telefono
                    tp_codicefiscale = anagrafica_privato.codicefiscale
                    tp_idanagraficaprivato = anagrafica_privato.idanagrafica
            else:
                return "Formato idanagrafica non valido."
            
                associazione = Associazioni.query.filter_by(idcontenzioso=idcontenzioso).first()

            idlegale = associazione.idlegale
            idlegaledue = associazione.idlegaledue
            
            legale = Legale.query.filter_by(idlegale=idlegale).first()
            legaledue = Legale.query.filter_by(idlegale=idlegaledue).first()
            
            tp_nome_legale = legale.nome
            tp_cognome_legale = legale.cognome
            tp_telefono_legale = legale.telefono
            tp_email_legale = legale.email
            tp_pec_legale = legale.pec
            tp_idlegale = legale.idlegale
            
            if legaledue is not None:
                tp_nome_legale_due = legaledue.nome
                tp_cognome_legale_due = legaledue.cognome
                tp_telefono_legale_due = legaledue.telefono
                tp_email_legale_due = legaledue.email
                tp_pec_legale_due = legaledue.pec
                tp_idlegale_due = legaledue.idlegale
            else:
                tp_nome_legale_due = ""
                tp_cognome_legale_due = ""
                tp_telefono_legale_due = ""
                tp_email_legale_due = ""
                tp_pec_legale_due = ""
                tp_idlegale_due = ""
                
            
        else:
            idanagrafica = None

        
        print(f"Contenzioso ID: {contenzioso.idcontenzioso}, Associazione ID: {idanagrafica}, Nome: {tp_nome}")

        idcontenzioso=contenzioso.idcontenzioso
        
        calendario = Calendario.query.filter_by(idcontenzioso=contenzioso.idcontenzioso).first()
        tp_dataudienza=None
        tp_dataudienza=calendario.data
        tp_preavvisoudienza=calendario.preavviso
        
        contenziosi_with_idanagrafica.append((contenzioso, idanagrafica, tp_dataudienza , tp_preavvisoudienza , tp_nome, tp_cognome, tp_email, tp_pec, tp_telefono, tp_codicefiscale, tp_ragsociale, tp_piva, tp_nome_legale, tp_nome_legale_due, tp_cognome_legale, tp_cognome_legale_due, tp_telefono_legale, tp_telefono_legale_due, tp_email_legale, tp_email_legale_due, tp_pec_legale, tp_pec_legale_due, tp_idlegale, tp_idlegale_due))

    return render_template('contenziosi.html', contenziosi=contenziosi_with_idanagrafica,
                               tp_ragsociale=tp_ragsociale if idanagrafica.startswith("AZ") else "",
                               tp_nome=tp_nome if idanagrafica.startswith("PP") else "",
                               tp_cognome=tp_cognome if idanagrafica.startswith("PP") else "",
                               tp_email=tp_email if idanagrafica.startswith("PP") else tp_email,
                               tp_pec=tp_pec if idanagrafica.startswith("PP") else tp_pec,
                               tp_telefono=tp_telefono if idanagrafica.startswith("PP") else tp_pec,
                               tp_codicefiscale=tp_codicefiscale if idanagrafica.startswith("PP") else tp_piva,
                               tp_nome_legale=tp_nome_legale, tp_cognome_legale=tp_cognome_legale,
                               tp_email_legale=tp_email_legale, tp_pec_legale=tp_pec_legale, tp_telefono_legale=tp_telefono_legale,
                               tp_nome_legale_due=tp_nome_legale_due, tp_cognome_legale_due=tp_cognome_legale_due,
                               tp_email_legale_due=tp_email_legale_due, tp_pec_legale_due=tp_pec_legale_due, tp_telefono_legale_due=tp_telefono_legale_due, tp_dataudienza=tp_dataudienza, tp_preavvisoudienza=tp_preavvisoudienza,
                               user=utente)

@app.route('/nuovo_contenzioso_ai')
def nuovo_contenzioso_ai():
    utente = session.get('user_name')
    idanagrafica = request.args.get('idanagrafica')
    return render_template('ai_contenzioso_upload.html',user=utente)

@app.route('/ai_upload', methods=['POST'])
def ai_upload():
    if 'file' not in request.files:
        return jsonify({"error": "Nessun file è stato caricato."}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "Non è stato selezionato nessun file."}), 400
    
    idanagrafica = request.form['idanagrafica']

    files = {'file': file.stream}
    response = requests.post(MINERVA_AI_ENDPOINT, files=files)
    
    if response.status_code != 200:
        return jsonify({"msgErrore": "Errore nella richiesta all'endpoint AI. Assicurarsi di aver caricato un file PDF. Se si sta utilizzando la versione DEMO assicurarsi di aver caricato uno dei file accettati. Per maggiori informazioni contattare l'amministratore."}), 500
    
    data = response.json()

    ai_annotributodue = data.get('annotributodue')
    ai_annotributouno = data.get('annotributouno')
    ai_dataprotocollo = data.get('dataprotocollo')
    ai_idavvocatoente = data.get('idavvocatoente')
    ai_message = data.get('message')
    ai_nomecompletoavvocatoente = data.get('nomecompletoavvocatoente')
    ai_numeroprotocollo = data.get('numeroprotocollo')
    ai_oggetto = data.get('oggetto')
    ai_pec = data.get('pec')
    ai_tipologia = data.get('tipologia')
    ai_valore = data.get('valore')


    url = url_for('nuovo_contenzioso', 
                  idanagrafica=idanagrafica, 
                  ai_annotributodue=ai_annotributodue,
                  ai_annotributouno=ai_annotributouno,
                  ai_dataprotocollo=ai_dataprotocollo,
                  ai_idavvocatoente=ai_idavvocatoente,
                  ai_message=ai_message,
                  ai_nomecompletoavvocatoente=ai_nomecompletoavvocatoente,
                  ai_numeroprotocollo=ai_numeroprotocollo,
                  ai_oggetto=ai_oggetto,
                  ai_pec=ai_pec,
                  ai_tipologia=ai_tipologia,
                  ai_valore=ai_valore)

    return redirect(url)


if __name__ == '__main__':
    app.run(debug=True)