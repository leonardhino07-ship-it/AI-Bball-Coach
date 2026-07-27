import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch
import sqlite3
import hashlib
import io
import re
import html
import datetime
import time
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 0. CONFIGURAZIONE PAGINA E GRAFICA (CSS)
# ==========================================
st.set_page_config(page_title="Basketball Coach PRO", page_icon="🏀", layout="wide")

# CSS personalizzato per un look moderno, pulito e intuitivo (tema basket)
st.markdown("""
<style>
    /* Sfondo generale e font */
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Colore dei titoli principali */
    h1, h2, h3 {
        color: #1a202c !important;
        font-weight: 800 !important;
    }
    
    /* Pulsanti (Stile Basket - Arancione) */
    .stButton > button {
        background-color: #ea580c !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(234, 88, 12, 0.2) !important;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #c2410c !important;
        box-shadow: 0 10px 15px -3px rgba(234, 88, 12, 0.3) !important;
        transform: translateY(-2px);
    }
    
    /* Stile delle card (Form e container) */
    [data-testid="stForm"] {
        background-color: white;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* Stile input fields per chiarezza */
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input, 
    .stSelectbox > div > div > div, 
    .stTextArea > div > div > textarea {
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #f8fafc !important;
    }
    .stTextInput > div > div > input:focus, 
    .stNumberInput > div > div > input:focus, 
    .stSelectbox > div > div > div:focus, 
    .stTextArea > div > div > textarea:focus {
        border-color: #ea580c !important;
        box-shadow: 0 0 0 1px #ea580c !important;
    }
    
    /* Stile dei tab (Menu in alto) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 2px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: transparent;
        font-size: 1.1rem;
        font-weight: 600;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        color: #ea580c !important;
        border-bottom: 3px solid #ea580c !important;
    }
    
    /* Alert e messaggi info */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. GESTIONE DATABASE LOCALE E MEMORIA UTENTI / SCHEDE
# ==========================================
def init_db():
    conn = sqlite3.connect('utenti_basket.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            email TEXT,
            giocatori_salvati TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS schede (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            data_creazione TEXT NOT NULL,
            titolo TEXT NOT NULL,
            contenuto TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def crea_utente(username, password, email):
    conn = sqlite3.connect('utenti_basket.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, email, giocatori_salvati) VALUES (?, ?, ?, ?)', 
                  (username, hash_password(password), email, ""))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_utente(username, password):
    conn = sqlite3.connect('utenti_basket.db')
    c = conn.cursor()
    c.execute('SELECT username, giocatori_salvati FROM users WHERE username=? AND password=?', (username, hash_password(password)))
    data = c.fetchone()
    conn.close()
    return data

def aggiorna_memoria_giocatori(username, giocatori):
    conn = sqlite3.connect('utenti_basket.db')
    c = conn.cursor()
    c.execute('UPDATE users SET giocatori_salvati=? WHERE username=?', (giocatori, username))
    conn.commit()
    conn.close()

def salva_scheda_db(username, titolo, contenuto):
    conn = sqlite3.connect('utenti_basket.db')
    c = conn.cursor()
    data_ora = datetime.datetime.now().strftime("%d/%m/%Y alle %H:%M")
    c.execute('INSERT INTO schede (username, data_creazione, titolo, contenuto) VALUES (?, ?, ?, ?)',
              (username, data_ora, titolo, contenuto))
    conn.commit()
    conn.close()

def get_schede_utente_db(username):
    conn = sqlite3.connect('utenti_basket.db')
    c = conn.cursor()
    c.execute('SELECT id, data_creazione, titolo, contenuto FROM schede WHERE username=? ORDER BY id DESC', (username,))
    data = c.fetchall()
    conn.close()
    return data

def elimina_scheda_db(scheda_id):
    conn = sqlite3Questo errore (**"source code string cannot contain null bytes"**) non dipende da un errore nella sintassi del codice stesso, ma da **come è stato salvato il file** sul tuo computer. 

Significa che Python sta leggendo dei caratteri invisibili (i "null bytes") che di solito compaiono per due motivi:
1. Hai usato un programma come Word, WordPad o TextEdit in formato "Rich Text" per salvare il codice, invece di un editor di testo semplice.
2. Il file è stato salvato con la codifica sbagliata (spesso UTF-16 invece della corretta **UTF-8**).

## Come risolvere l'errore del file

Per ripulire il file da questi caratteri invisibili, segui questi passaggi:

1. **Apri un editor di testo semplice o per programmatori** (come il Blocco Note su Windows, TextEdit in formato "Solo testo" su Mac, Notepad++ o VS Code). Non usare programmi di videoscrittura.
2. **Crea un nuovo file vuoto**.
3. **Incolla il codice** all'interno del nuovo file.
4. Vai su "Salva con nome..." e assicurati che l'opzione "Codifica" (Encoding) sia impostata su **UTF-8**.
5. Salva il file sostituendo quello vecchio.

## Dove dovevi sostituire il codice?

Poiché ogni conversazione qui riparte da zero, **non ho lo storico della tua chat precedente** e non posso vedere il codice che ti era stato generato né il file originale a cui stavi lavorando.

Per poterti indicare il punto esatto in cui inserire o sostituire il codice:
* Incollami qui il codice che ti è stato fornito.
* Incollami il tuo script originale (o la parte rilevante) in cui stavi cercando di integrarlo.

<FollowUp label="Vuoi incollarmi il codice così lo sistemiamo insieme?" query="Ecco il codice che stavo cercando di usare e lo script originale in cui devo inserirlo:" />
