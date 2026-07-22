import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch
import sqlite3
import hashlib

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach PRO", page_icon="🏀", layout="wide")

# ==========================================
# 1. GESTIONE DATABASE LOCALE E MEMORIA UTENTI
# ==========================================
def init_db():
    conn = sqlite3.connect('utenti_basket.db')
    c = conn.cursor()
    # Creazione tabella utenti se non esiste
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            email TEXT,
            giocatori_salvati TEXT
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
        return False # Il nome utente esiste già
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

# Inizializza il database all'avvio
init_db()

# Inizializza le variabili di sessione
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'giocatori_memoria' not in st.session_state:
    st.session_state['giocatori_memoria'] = ''

# ==========================================
# 2. SCHERMATA DI LOGIN / REGISTRAZIONE
# ==========================================
if not st.session_state['logged_in']:
    st.title("🏀 Benvenuto in AI Basketball Coach PRO")
    st.write("Accedi o crea un account per iniziare il tuo percorso e salvare le tue preferenze.")
    
    tab_login, tab_register = st.tabs(["🔑 Accedi", "📝 Registrati (Nuovo Account)"])
    
    with tab_login:
        st.subheader("Fai il Login")
        log_user = st.text_input("Username", key="log_user")
        log_pass = st.text_input("Password", type="password", key="log_pass")
        
        # Pulsanti "Finti" per far capire l'intenzione futura (Google/Apple richiedono API terze)
        st.info("💡 L'accesso con Google, Apple o Numero di telefono sarà attivato collegando un server cloud (es. Firebase/Supabase).")
        
        if st.button("Accedi"):
            user_data = login_utente(log_user, log_pass)
            if user_data:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_data[0]
                st.session_state['giocatori_memoria'] = user_data[1]
                st.success(f"Bentornato {user_data[0]}!")
                st.rerun()
            else:
                st.error("Username o Password errati.")

    with tab_register:
        st.subheader("Crea il tuo profilo unico")
        reg_user = st.text_input("Scegli un Username Unico (es. Coach_Mamba8)")
        reg_email = st.text_input("Email")
        reg_pass = st.text_input("Scegli una Password", type="password")
        
        st.write("📸 **Foto Profilo** (Opzionale)")
        metodo_foto = st.radio("Come vuoi caricare la foto?", ["Carica dalla Galleria", "Scatta una foto ora"])
        if metodo_foto == "Carica dalla Galleria":
            foto_profilo = st.file_uploader("Scegli un'immagine", type=['jpg', 'jpeg', 'png'])
        else:
            foto_profilo = st.camera_input("Scatta una foto con la fotocamera")
            
        if st.button("Crea Account"):
            if reg_user and reg_pass:
                successo = crea_utente(reg_user, reg_pass, reg_email)
                if successo:
                    st.success("Account creato con successo! Ora puoi fare il login.")
                else:
                    st.error("⚠️ Questo Username è già in uso! Scegline un altro.")
            else:
                st.warning("Inserisci Username e Password validi.")

# ==========================================
# 3. L'APP PRINCIPALE (Accessibile solo se loggati)
# ==========================================
else:
    # Intestazione utente loggato
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.title(f"🏀 AI Basketball Coach PRO - Profilo di {st.session_state['username']}")
    with col_head2:
        if st.button("🚪 Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.write("Programmazione settimanale bilanciata con link YouTube DIRETTI e REALI.")

    # Controllo chiave API
    if "GROQ_API_KEY" in st.secrets:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    else:
        st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
        st.stop()

    client = Groq(api_key=groq_api_key)

    # Motore YouTube originale
    def cerca_video_drills_raw(giocatori, obiettivo):
        db_video_text = ""
        queries = []
        lista_g = [g.strip() for g in giocatori.split(',') if g.strip()]
        for g in lista_g:
            queries.append(f"{g} signature basketball move drill tutorial")
            queries.append(f"{g} footwork breakdown")
        if obiettivo:
            queries.append(f"basketball {obiettivo} drill tutorial")
        for q in queries[:4]:
            try:
                search = VideosSearch(q, limit=2)
                results = search.result().get('result', [])
                for vid in results:
                    v_id = vid.get('id')
                    title = vid.get('title', 'Tutorial Esercizio')
                    if v_id:
                        clean_url = f"https://www.youtube.com/watch?v={v_id}"
                        db_video_text += f"\n- TITOLO VIDEO: \"{title}\"\n  LINK ESATTO DA COPIARE: {clean_url}\n"
            except Exception:
                pass
        return db_video_text if db_video_text else "NESSUN VIDEO TROVATO. NON INSERIRE ALCUN LINK YOUTUBE."

    with st.form("coach_form"):
        st.subheader("Parametri del Giocatore e Programmazione")
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome del giocatore", value=st.session_state['username'])
            eta = st.number_input("Età", min_value=5, max_value=60, value=18)
            ruolo = st.selectbox("Ruolo principale", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
            livello = st.selectbox("Livello di gioco", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
        
        with col2:
            obiettivo = st.text_input("Obiettivo preciso (es. primo passo esplosivo, handles/palleggio, tiro dal palleggio)")
            frequenza = st.selectbox("Frequenza settimanale", ["1-2 volte", "3-4 volte", "5+ volte"])
            durata_singola = st.radio("Durata esatta singola sessione:", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
            logistica = st.radio("Logistica di allenamento:", ["Da solo", "In compagnia"])

        st.subheader("Film Study & Giocatori Modello")
        # QUI L'IA SI RICORDA I DATI: il "value" è precompilato con i dati del database
        giocatori_simili = st.text_input("A chi ti ispiri? (Separa con virgola. Es: Stephen Curry)", value=st.session_state['giocatori_memoria'])
        note_extra = st.text_area("Note (es. infortuni, attrezzi a disposizione come coni, pallina da tennis)")
        
        submit_button = st.form_submit_button(label="Genera Programmazione Settimanale Sicura")

    if submit_button:
        # AGGIORNA LA MEMORIA: Se l'utente ha inserito nuovi giocatori, li salva nel database per le prossime volte
        aggiorna_memoria_giocatori(st.session_state['username'], giocatori_simili)
        st.session_state['giocatori_memoria'] = giocatori_simili

        with st.spinner("Estrazione dei link YouTube diretti in corso..."):
            database_video_reali = cerca_video_drills_raw(giocatori_simili, obiettivo)

        with st.spinner("L'IA sta costruendo la scheda garantendo pari dettaglio per OGNI giorno..."):
            prompt = f"""
            Sei un MENTORE E PREPARATORE ATLETICO NBA di livello mondiale.
            Il tuo compito è creare un PROGRAMMA DI ALLENAMENTO SETTIMANALE iper-dettagliato.

            DATI UTENTE TASSATIVI:
            - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
            - OBIETTIVO PRINCIPALE: {obiettivo}
            - FREQUENZA SETTIMANALE: {frequenza}
            - DURATA SINGOLA SESSIONE: {durata_singola}
            - LOGISTICA: {logistica} (SE "DA SOLO": VIETATI PASSAGGI E DIFENSORI REALI)
            - GIOCATORI MODELLO: {giocatori_simili}
            - NOTE/ATTREZZATURA: {note_extra}

            DATABASE LINK YOUTUBE (REALI E VERIFICATI):
            {database_video_reali}

            REGOLE FERREE ED INDISPENSIBILI (PENA IL FALLIMENTO DELL'ALLENAMENTO):

            1. DIVIETO ASSOLUTO DI INVENTARE LINK (ANTI-HALLUCINATION):
               È SEVERAMENTE VIETATO inventare link YouTube. 
               È SEVERAMENTE VIETATO utilizzare l'ID "dQw4w9WgXcQ" o qualsiasi altro link non presente nel DATABASE qui sopra.
               Se per un esercizio ritieni utile un video, prendi ESATTAMENTE il "LINK ESATTO DA COPIARE" e scrivilo così:
               👉 **Video di riferimento:** https://www.youtube.com/watch?v=...
               Se non hai un video pertinente nel database, NON inserire alcun link.

            2. REGOLA DI UNIFORMITÀ DEI GIORNI (TASSATIVO):
               In base alla frequenza scelta ({frequenza}), devi creare tutti i giorni previsti.
               Ogni singolo giorno deve contenere la stessa quantità di dettagli, serie, ripetizioni e spiegazione biomeccanica. 

            3. RISPETTO RIGIDO DEL TEMPO ({durata_singola}):
               Ogni giorno deve coprire la durata totale di {durata_singola}.
               Tutti gli esercizi di TUTTI i giorni devono avere indicati: [Durata in min | Serie | Ripetizioni | Recupero].
            """

            try:
                chat_completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Sei un Master Coach NBA. Inserisci solo link in puro testo tratti unicamente dal database fornito. Non inventi mai link YouTube."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2, 
                    max_tokens=4500
                )
                
                scheda = chat_completion.choices[0].message.content
                st.success("Programmazione Settimanale Uniforme generata!")
                st.markdown("---")
                st.markdown(scheda)
                
            except Exception as e:
                st.error(f"Si è verificato un errore: {e}")
