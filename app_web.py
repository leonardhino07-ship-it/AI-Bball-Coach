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

# Inizializza DB e Session State
init_db()

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
        
        st.info("💡 L'accesso sociale (Google, Apple, SMS) sarà integrabile via cloud authentication.")
        
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
        reg_user = st.text_input("Scegli un Username Unico")
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
# 3. APP PRINCIPALE (Accessibile solo se loggati)
# ==========================================
else:
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.title(f"🏀 AI Basketball Coach PRO - Profilo di {st.session_state['username']}")
    with col_head2:
        if st.button("🚪 Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.write("Programmazione settimanale Elite con calcolo rigoroso del volume e link video YouTube verificati.")

    if "GROQ_API_KEY" in st.secrets:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    else:
        st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
        st.stop()

    client = Groq(api_key=groq_api_key)

    # RICERCA YOUTUBE RIGIDA CON FILTRO DI VALIDITÀ VIDEO
    def cerca_video_youtube_dettagliati(giocatori, obiettivo):
        video_found = []
        queries = []
        
        lista_g = [g.strip() for g in giocatori.split(',') if g.strip()]
        
        for g in lista_g:
            queries.append(f"{g} basketball drill breakdown")
            queries.append(f"{g} basketball workout tutorial")

        if obiettivo:
            queries.append(f"best basketball {obiettivo} drill tutorial")

        for q in queries[:4]:
            try:
                search = VideosSearch(q, limit=3)
                results = search.result().get('result', [])
                for vid in results:
                    v_id = vid.get('id')
                    v_type = vid.get('type', 'video')
                    title = vid.get('title', 'Tutorial Esercizio Basketball')
                    views = vid.get('viewCount', {}).get('text', 'Molte visualizzazioni') if isinstance(vid.get('viewCount'), dict) else "Molte visualizzazioni"
                    
                    # ACCETTA ESCLUSIVAMENTE VIDEO SINGOLI REALI E FUNZIONANTI (NO PLAYLIST, NO CANALI, NO RICKROLL)
                    if v_id and v_type == 'video' and v_id != "dQw4w9WgXcQ":
                        clean_url = f"https://www.youtube.com/watch?v={v_id}"
                        video_found.append({
                            "title": title,
                            "url": clean_url,
                            "views": views
                        })
            except Exception:
                pass

        if not video_found:
            return "NESSUN VIDEO DISPONIBILE. OMETTI LA RIGA DEI VIDEO SE NON PERTINENTE."

        formatted_text = "ELENCO VIDEO DISPONIBILI SU YOUTUBE (UTILIZZA SOLO QUESTI URL SENZA MODIFICARLI):\n"
        for idx, v in enumerate(video_found, 1):
            formatted_text += f"{idx}. TITOLO: \"{v['title']}\" | VISUALIZZAZIONI: {v['views']} | URL: {v['url']}\n"

        return formatted_text

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
        giocatori_simili = st.text_input("A chi ti ispiri? (Separa con virgola. Es: Stephen Curry, Kobe Bryant)", value=st.session_state['giocatori_memoria'])
        note_extra = st.text_area("Note (es. infortuni, attrezzi a disposizione come coni, pallina da tennis)")
        
        submit_button = st.form_submit_button(label="Genera Scheda di Allenamento Elite")

    if submit_button:
        # Salva i giocatori preferiti nel profilo utente
        aggiorna_memoria_giocatori(st.session_state['username'], giocatori_simili)
        st.session_state['giocatori_memoria'] = giocatori_simili

        with st.spinner("Ricerca ed analisi dei video più popolari di basket su YouTube in corso..."):
            risultati_youtube = cerca_video_youtube_dettagliati(giocatori_simili, obiettivo)

        with st.spinner("L'IA sta costruendo la scheda leggendo TUTTI i parametri inseriti..."):
            prompt = f"""
            Sei un MASTER COACH E PREPARATORE ATLETICO NBA DI LIVELLO MONDIALE.
            Il tuo compito è analizzare TUTTI I DATI INSERITI DALL'UTENTE e costruire un programma settimanale impeccabile, sia nella calibrazione del tempo che nel livello di dettaglio.

            DATI UTENTE TASSATIVI DA INCLUDERE NELLA SCHEDA:
            - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
            - OBIETTIVO PRINCIPALE: {obiettivo}
            - FREQUENZA SETTIMANALE: {frequenza}
            - DURATA SINGOLA SESSIONE: {durata_singola}  <-- REGOLA DI VOLUME FONDAMENTALE!
            - LOGISTICA: {logistica} (Se 'Da solo', VIETATI passaggi e difensori reali)
            - GIOCATORI MODELLO: {giocatori_simili}
            - NOTE/ATTREZZI: {note_extra}

            DATABASE VIDEO YOUTUBE VERIFICATI:
            {risultati_youtube}

            REGOLE FERREE ED INDISPENSIBILI:

            1. CALCOLO TASSATIVO DEL VOLUME IN BASE ALLA DURATA ({durata_singola}):
               È SEVERAMENTE VIETATO generare solo 2 o 3 esercizi se la durata è di 1 ora o più!
               Devi riempire l'intero minutaggio di {durata_singola} seguendo questa tabella rigida di esercizi PER OGNI GIORNO:
               - Se "1 ora" (60 min): inserisci 4-5 esercizi totali.
               - Se "1 ora e 30" (90 min): inserisci 6-7 esercizi totali.
               - Se "2 ore" (120 min) o più: INSERISCI ALMENO 7-9 ESERCIZI DISTINTI divisi in:
                 * Riscaldamento / Attivazione (15 min - 2 esercizi)
                 * Blocco 1: Tecnica & Signature Drills da {giocatori_simili} (45 min - 3 esercizi)
                 * Blocco 2: Applicazione ad alta intensità / Tiro / Situazionale per {obiettivo} (45 min - 3 esercizi)
                 * Defaticamento & Mobilità (15 min - 1 esercizio)

            2. STRUTTURA TASSATIVA PER OGNI ESERCIZIO:
               Tutti gli esercizi di TUTTI i giorni devono includere esattamente questi 7 campi:
               - **Nome Esercizio:** [Nome evocativo e professionale]
               - **Durata stimata & Serie:** [es. 12 minuti | 4 Serie | 10 Ripetizioni per lato | Recupero 60 sec]
               - **🎯 Cosa allena nello specifico:** [Dettaglia il gesto tecnico/motorio esatto]
               - **⭐ Perché è stato scelto ("Best of the Best"):** [Spiega la motivazione tecnica in relazione a {obiettivo} e {giocatori_simili}]
               - **⚙️ Spiegazione Biomeccanica e Tecnica:** [Dettaglio su postura, piedi, baricentro e palla]
               - **🎥 Video di riferimento:** [Incolla l'URL esatto dal database e aggiungi il minutaggio. Es: https://www.youtube.com/watch?v=ID_VIDEO&t=90s (Guarda dal minuto 1:30)]

            3. RISPETTO TOTALE DI OGNI PARAMETRO UTENTE:
               La scheda deve fare esplicito riferimento all'età ({eta}), al ruolo ({ruolo}) e alla logistica ({logistica}). Se si allena da solo, adatta l'esercizio in modo che possa farlo in autonomia.

            4. UNIFORMITÀ DEI GIORNI:
               Crea tutte le sezioni dei giorni ("### GIORNO 1", "### GIORNO 2", ecc.) previste dalla frequenza ({frequenza}). Il Giorno 2, 3 e successivi DEVONO contenere lo STESSO IDENTICO livello di dettaglio e numero di esercizi del Giorno 1.
            """

            try:
                chat_completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Sei un Master Coach NBA. Rispetti al 100% il minutaggio della sessione, creando il numero corretto di esercizi (almeno 7-9 esercizi per 2 ore). Usi solo link video funzionanti e leggi tutti i parametri dell'utente."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=4500
                )
                
                scheda = chat_completion.choices[0].message.content
                st.success("Programmazione Settimanale Elite generata con successo!")
                st.markdown("---")
                st.markdown(scheda)
                
            except Exception as e:
                st.error(f"Si è verificato un errore: {e}")
