import streamlit as st
import groq
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
# 0. CONFIGURAZIONE PAGINA E GRAFICA (MOBILE-FRIENDLY)
# ==========================================
st.set_page_config(page_title="Basketball Coach PRO", layout="wide")

# CSS minimalista, pulito e ottimizzato per smartphone
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    h1, h2, h3 {
        color: #111827 !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    .stButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 0.85rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        width: 100%;
        margin-top: 10px;
    }
    .stButton > button:active {
        background-color: #374151 !important;
    }
    
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input, 
    .stSelectbox > div > div > div, 
    .stTextArea > div > div > textarea {
        border-radius: 4px !important;
        border: 1px solid #d1d5db !important;
        background-color: #f9fafb !important;
        color: #111827 !important;
        padding: 0.6rem !important;
    }
    .stTextInput > div > div > input:focus, 
    .stNumberInput > div > div > input:focus, 
    .stSelectbox > div > div > div:focus, 
    .stTextArea > div > div > textarea:focus {
        border-color: #000000 !important;
        box-shadow: none !important;
    }
    
    [data-testid="stForm"] {
        background-color: #ffffff;
        padding: 1.25rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #e5e7eb;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 16px;
        background-color: transparent;
        font-size: 0.95rem;
        font-weight: 600;
        color: #6b7280;
    }
    .stTabs [aria-selected="true"] {
        color: #000000 !important;
        border-bottom: 2px solid #000000 !important;
    }
    
    hr {
        border-color: #e5e7eb !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATABASE LOCALE
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
    conn = sqlite3.connect('utenti_basket.db')
    c = conn.cursor()
    c.execute('DELETE FROM schede WHERE id=?', (scheda_id,))
    conn.commit()
    conn.close()

init_db()

# Stato sessione
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'giocatori_memoria' not in st.session_state:
    st.session_state['giocatori_memoria'] = ''
if 'scheda_generata' not in st.session_state:
    st.session_state['scheda_generata'] = ''
if 'nome_atleta_scheda' not in st.session_state:
    st.session_state['nome_atleta_scheda'] = ''

# ==========================================
# 2. ESPORTAZIONE PDF
# ==========================================
def pulisci_e_formatta_testo_pdf(testo):
    testo_pulito = re.sub(r'[^a-zA-Z0-9\s\.,;:!\?\-\(\)\[\]"\'/%\&\=\_\#\+àèéìòùÀÈÉÌÒÙáéíóúÁÉÍÓÚ]', '', testo)
    testo_escaped = html.escape(testo_pulito)
    testo_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', testo_escaped)
    testo_formatted = re.sub(r'\*(.*?)\*', r'<i>\1</i>', testo_formatted)
    return testo_formatted

def genera_pdf_scheda(testo_scheda, nome_utente):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=15, leading=18, textColor=colors.HexColor('#000000'), spaceAfter=8)
    h2_style = ParagraphStyle('SectionH2', parent=styles['Heading2'], fontSize=12, leading=15, textColor=colors.HexColor('#111827'), spaceBefore=10, spaceAfter=4)
    h3_style = ParagraphStyle('SectionH3', parent=styles['Heading3'], fontSize=10, leading=13, textColor=colors.HexColor('#374151'), spaceBefore=8, spaceAfter=2)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=9.5, leading=13, textColor=colors.HexColor('#111827'), spaceAfter=4)

    story = []
    story.append(Paragraph("<b>BASKETBALL COACH PRO - SCHEDA DI PREPARAZIONE INTEGRALE</b>", title_style))
    story.append(Paragraph(f"<b>Atleta:</b> {html.escape(nome_utente)}", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#000000'), spaceBefore=4, spaceAfter=10))
    
    righe = testo_scheda.split('\n')
    for riga in righe:
        riga_str = riga.strip()
        if not riga_str:
            story.append(Spacer(1, 3))
            continue
            
        if riga_str.startswith('### '):
            story.append(Paragraph(pulisci_e_formatta_testo_pdf(riga_str.replace('### ', '')), h3_style))
        elif riga_str.startswith('## '):
            story.append(Paragraph(pulisci_e_formatta_testo_pdf(riga_str.replace('## ', '')), h2_style))
        elif riga_str.startswith('# '):
            story.append(Paragraph(pulisci_e_formatta_testo_pdf(riga_str.replace('# ', '')), title_style))
        elif riga_str.startswith('---'):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.gray, spaceBefore=4, spaceAfter=4))
        else:
            story.append(Paragraph(pulisci_e_formatta_testo_pdf(riga_str), body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================================
# 3. AUTENTICAZIONE
# ==========================================
if not st.session_state['logged_in']:
    st.title("Basketball Coach PRO")
    st.write("Accedi o crea un account per generare la tua programmazione tecnica e fisica.")
    
    tab_login, tab_register = st.tabs(["Accedi", "Registrati"])
    
    with tab_login:
        log_user = st.text_input("Username", key="log_user")
        log_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Accedi"):
            user_data = login_utente(log_user, log_pass)
            if user_data:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user_data[0]
                st.session_state['giocatori_memoria'] = user_data[1]
                st.success(f"Autenticato come {user_data[0]}")
                st.rerun()
            else:
                st.error("Credenziali non valide.")

    with tab_register:
        reg_user = st.text_input("Scegli un Username")
        reg_email = st.text_input("Email")
        reg_pass = st.text_input("Scegli una Password", type="password")
        if st.button("Crea Account"):
            if reg_user and reg_pass:
                if crea_utente(reg_user, reg_pass, reg_email):
                    st.success("Account registrato. Esegui il login.")
                else:
                    st.error("Username non disponibile.")
            else:
                st.warning("Compila tutti i campi richiesti.")

# ==========================================
# 4. PANNELLO PRINCIPALE
# ==========================================
else:
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title(f"Atleta: {st.session_state['username']}")
    with col_head2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Disconnetti"):
            st.session_state['logged_in'] = False
            st.session_state['scheda_generata'] = ''
            st.rerun()

    if "GROQ_API_KEY" in st.secrets:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    else:
        st.error("GROQ_API_KEY non configurata nei Secrets.")
        st.stop()

    client = Groq(api_key=groq_api_key)

    def cerca_video_youtube_dettagliati(giocatori, obiettivo):
        video_found = []
        queries = []
        lista_g = [g.strip() for g in giocatori.split(',') if g.strip()]
        for g in lista_g:
            queries.append(f"{g} basketball drill breakdown methodology")
            queries.append(f"{g} elite basketball workout tutorial")
        if obiettivo:
            queries.append(f"best elite basketball {obiettivo} drill tutorial pro")

        for q in queries[:3]:
            try:
                search = VideosSearch(q, limit=2)
                results = search.result().get('result', [])
                for vid in results:
                    if vid.get('title', ''):
                        video_found.append(vid.get('title'))
            except Exception:
                pass

        if not video_found:
            return "Nessun dato estratto dal web, procedi con il know-how dei Preparatori Atletici e Head Coach d'élite."
        return "Riferimenti tecnici estratti:\n" + "\n".join([f"- {t}" for t in video_found])

    main_tab1, main_tab2 = st.tabs(["Prepara Programma", "Archivio Schede"])

    with main_tab1:
        st.write("Inserisci i dati tecnici e fisici per generare la programmazione.")

        with st.form("coach_form"):
            st.markdown("### Dati Anagrafici e Cestistici")
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome Atleta", value=st.session_state['username'])
                eta = st.number_input("Età", min_value=5, max_value=60, value=18)
                ruolo = st.selectbox("Ruolo in Campo", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
                livello = st.selectbox("Livello Agonistico", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
            with col2:
                obiettivo = st.text_input("Obiettivo Specifico (es. primo passo esplosivo, arresto e tiro, letture pick&roll)")
                frequenza = st.selectbox("Frequenza Settimanale", ["1-2 volte", "3-4 volte", "5+ volte"])
                durata_singola = st.selectbox("Durata della Singola Sessione", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
                logistica = st.selectbox("Modalità di Lavoro", ["Da solo", "In compagnia"])

            st.markdown("### Condizioni Fisiche e Ispirazione")
            col3, col4 = st.columns(2)
            with col3:
                giocatori_simili = st.text_input("Giocatori/Atleti di riferimento", value=st.session_state['giocatori_memoria'])
            with col4:
                note_extra = st.text_area("Infortuni, limitazioni fisiche o di attrezzatura (Es: sovraccarico al ginocchio, solo 1 pallone, no palestra pesi)")
            
            submit_button = st.form_submit_button(label="Genera Programma Integrale")

        if submit_button:
            aggiorna_memoria_giocatori(st.session_state['username'], giocatori_simili)
            st.session_state['giocatori_memoria'] = giocatori_simili
            st.session_state['nome_atleta_scheda'] = nome

            num_giorni = 2
            if "3-4" in frequenza: num_giorni = 4
            elif "5+" in frequenza: num_giorni = 5

            with st.spinner("Ricerca metodologie e strutturazione scheda..."):
                risultati_youtube = cerca_video_youtube_dettagliati(giocatori_simili, obiettivo)

            progress_bar = st.progress(0)
            status_text = st.empty()

            scheda_completa = f"# PROGRAMMAZIONE INTEGRALE - {nome.upper()}\n"
            scheda_completa += f"**Ruolo:** {ruolo} | **Livello:** {livello} | **Età:** {eta} anni | **Obiettivo Primario:** {obiettivo}\n"
            scheda_completa += f"**Frequenza:** {frequenza} ({num_giorni} giorni) | **Durata Sessione:** {durata_singola} | **Modalità:** {logistica}\n"
            scheda_completa += f"**Condizioni Fisiche/Logistica:** {note_extra}\n"
            scheda_completa += f"**Ispirazione Atleti:** {giocatori_simili}\n\n---\n\n"

            errore_generazione = False

            # GESTIONE DINAMICA E TASSATIVA DELLA LOGISTICA
            vincolo_logistica = ""
            if logistica == "Da solo":
                vincolo_logistica = "REGOLA LOGISTICA INVALICABILE: L'ATLETA SI ALLENA TOTALMENTE DA SOLO. E' FISICAMENTE IMPOSSIBILE AVERE UN COMPAGNO O UN COACH SUL CAMPO. È ASSOLUTAMENTE VIETATO INSERIRE ESERCIZI CHE RICHIEDANO PASSATORI O DIFENSORI REALI. SOSTITUISCI I COMPAGNI ESCLUSIVAMENTE CON SEDIE, CONI, AUTO-PASSAGGI CON EFFETTO SUL PARQUET O USO DEL TABELLONE."
            else:
                vincolo_logistica = "REGOLA LOGISTICA: L'atleta si allena in compagnia. Puoi includere liberamente esercizi che prevedono un passatore, un difensore o un coach attivo nella seduta."

            try:
                for giorno_idx in range(1, num_giorni + 1):
                    status_text.text(f"Sviluppo Giorno {giorno_idx} di {num_giorni}...")
                    
                    esercizi_gia_inseriti = scheda_completa[-2500:] if giorno_idx > 1 else "Nessun esercizio precedente."

                    prompt_giorno = f"""
                    Agisci simultaneamente come HEAD COACH (tecnica, tattica e decision-making) e PREPARATORE ATLETICO/FISICO (prevenzione, forza esplosiva, biomeccanica e mobilizzazione) di livello professionistico.
                    NON MENZIONARE MAI DI ESSERE UN'IA, UN MODELLO O UN PROGRAMMA. PARLA DIRETTAMENTE COME UN TEAM DI COACH PROFESSIONISTI. NESSUN SALUTO INIZIALE TIPO "CIAO", VAI DRITTO AL PIANO.

                    Struttura il **GIORNO {giorno_idx}** della programmazione.

                    LETTURA COMPLETA E RIGOROSA DEI DATI INSERITI DALL'UTENTE:
                    - Atleta: {nome}
                    - Età: {eta} anni (TASSATIVO: calibra l'intensità e la prevenzione in base a quest'età)
                    - Ruolo: {ruolo} (TASSATIVO: includi dettagli specifici per la posizione in campo)
                    - Livello: {livello} (TASSATIVO: adegua la complessità degli esercizi)
                    - Obiettivo Primario: {obiettivo} (deve essere il punto centrale della seduta)
                    - Limitazioni Fisiche / Infortuni / Note: {note_extra} (TASSATIVO: rispetta categoricamente ogni infortunio o vincolo logistico)
                    - Giocatori Ispirazione: {giocatori_simili}
                    - DURATA TASSATIVA RICHISTA: {durata_singola}

                    {vincolo_logistica}

                    REGOLE FONDAMENTALI ED ERMETICHE:
                    1. DIVIETO ASSOLUTO DI ESSERE RIASSUNTIVO: Esprimiti al massimo livello di dettaglio. Ogni esercizio deve contenere dettagli tecnici approfonditi, sia sul piano fisico/atletico che su quello cestistico. Spiega i movimenti, le posture e i motivi biomeccanici.
                    2. CALCOLO MATEMATICO DELLA DURATA ({durata_singola}):
                       - La somma dei minuti di TUTTI gli esercizi (riscaldamento, lavoro atletico, lavoro tecnico, riposi tra le serie, idratazione e defaticamento) DEVE CORRISPONDERE ESATTAMENTE A {durata_singola}.
                       - Se l'utente richiede 2 ore (120 minuti), fornisci un numero corposo di esercizi divisi in blocchi realistici.
                    3. ZERO EMOJI E ZERO COMPAGNI SE "DA SOLO": Rispetta alla lettera il vincolo logistico fornito sopra.
                    4. EVITA RIPETIZIONI: Non ripetere gli stessi identici esercizi dei giorni scorsi: {esercizi_gia_inseriti}
                    5. STRUTTURA DETTAGLIATA PER OGNI ESERCIZIO:
                       - Nome Esercizio: [Nome professionale]
                       - Durata e Volume: [Minuti esatti, Serie x Ripetizioni, Tempi di Recupero]
                       - Dettaglio Preparatore Fisico: [Focus su forza, stabilità, catena cinetica, prevenzione o esplosività]
                       - Dettaglio Head Coach: [Focus tecnico su footwork, angolo di stacco, tiro, maneggio palla o letture]
                       - Esecuzione e Biomeccanica: [Descrizione passo-passo del movimento]
                       - Errori da Evitare: [Istruzioni correttive dirette]

                    Scrivi una scheda rigorosa, approfondita e priva di riassunti.
                    """

                    system_prompt = (
                        "Sei una figura combinata d'élite: un Head Coach di pallacanestro e un Preparatore Atletico e Fisico di livello professionale. "
                        "Non rivelare mai la tua natura artificiale e non usare mai emoji. "
                        "Rispetta CATEGORICAMENTE le direttive logistiche: se un utente si allena da solo, non inserire NESSUN esercizio con terze persone. "
                        "Non essere mai riassuntivo. Fornisci descrizioni estese, trasparenti e matematicamente precise rispetto al tempo totale richiesto."
                    )

                    try:
                        chat_completion = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt_giorno}
                            ],
                            temperature=0.2,
                            max_tokens=2500
                        )
                        
                        testo_giorno = chat_completion.choices[0].message.content
                        testo_giorno = re.sub(r'[^\w\s.,;:!\?\-\(\)\[\]"\'/%\&\=\_\#\+àèéìòùÀÈÉÌÒÙáéíóúÁÉÍÓÚ]', '', testo_giorno)
                        
                        scheda_completa += f"## GIORNO {giorno_idx}\n\n" + testo_giorno + "\n\n---\n\n"
                        
                        progress_bar.progress(giorno_idx / num_giorni)
                        time.sleep(1.5)
                        
                    except groq.RateLimitError:
                        st.error("Limite di richieste/token API raggiunto (Rate Limit). Attendi 1 o 2 minuti prima di rigenerare la scheda per consentire al sistema di resettare i limiti.")
                        errore_generazione = True
                        break
                    except groq.APIError as e:
                        st.error(f"Errore nella comunicazione con il server API: {e}")
                        errore_generazione = True
                        break

                status_text.empty()
                progress_bar.empty()
                
                if not errore_generazione:
                    st.session_state['scheda_generata'] = scheda_completa
                    titolo_scheda = f"Scheda {obiettivo} ({frequenza} - {durata_singola})"
                    salva_scheda_db(st.session_state['username'], titolo_scheda, scheda_completa)

            except Exception as e:
                st.error("Si è verificato un errore generico. Verifica la connessione e riprova.")

        if st.session_state['scheda_generata']:
            st.success("Programma generato e salvato in Archivio.")
            st.markdown("---")
            st.markdown(st.session_state['scheda_generata'])
            
            st.markdown("---")
            st.subheader("Download Scheda PDF")
            
            nome_file = st.session_state['nome_atleta_scheda'] if st.session_state['nome_atleta_scheda'] else st.session_state['username']
            pdf_bytes = genera_pdf_scheda(st.session_state['scheda_generata'], nome_file)
            
            st.download_button(
                label="Scarica PDF Completo",
                data=pdf_bytes,
                file_name=f"Programma_Basket_{nome_file.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

    with main_tab2:
        st.write("Consulta le schede d'allenamento archiviate.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        schede_salvate = get_schede_utente_db(st.session_state['username'])
        
        if not schede_salvate:
            st.info("Nessuna scheda presente in archivio.")
        else:
            opzioni_schede = {f"{s[1]} - {s[2]}": s for s in schede_salvate}
            scheda_selezionata_label = st.selectbox("Seleziona dalla cronologia:", list(opzioni_schede.keys()))
            
            scheda_dati = opzioni_schede[scheda_selezionata_label]
            scheda_id = scheda_dati[0]
            scheda_data = scheda_dati[1]
            scheda_titolo = scheda_dati[2]
            scheda_testo = scheda_dati[3]
            
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                pdf_salvato = genera_pdf_scheda(scheda_testo, st.session_state['username'])
                st.download_button(
                    label="Scarica PDF",
                    data=pdf_salvato,
                    file_name=f"Scheda_{st.session_state['username']}_{scheda_id}.pdf",
                    mime="application/pdf",
                    key=f"dl_{scheda_id}"
                )
            with col_btn2:
                if st.button("Elimina", key=f"del_{scheda_id}"):
                    elimina_scheda_db(scheda_id)
                    st.success("Scheda eliminata.")
                    st.rerun()
            
            st.markdown("---")
            st.markdown(scheda_testo)
