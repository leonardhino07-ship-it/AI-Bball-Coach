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
# 0. CONFIGURAZIONE PAGINA E GRAFICA (MOBILE-FRIENDLY)
# ==========================================
st.set_page_config(page_title="Basketball Coach PRO", layout="wide")

# CSS minimalista, pulito e ottimizzato per smartphone
st.markdown("""
<style>
    /* Sfondo e font di base */
    .stApp {
        background-color: #ffffff;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Titoli puliti e professionali */
    h1, h2, h3 {
        color: #111827 !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    /* Pulsanti ottimizzati per il tocco (Mobile) */
    .stButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        width: 100%;
        margin-top: 10px;
    }
    .stButton > button:active {
        background-color: #374151 !important;
    }
    
    /* Input fields minimalisti */
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input, 
    .stSelectbox > div > div > div, 
    .stTextArea > div > div > textarea {
        border-radius: 4px !important;
        border: 1px solid #d1d5db !important;
        background-color: #f9fafb !important;
        color: #111827 !important;
        padding: 0.5rem !important;
    }
    .stTextInput > div > div > input:focus, 
    .stNumberInput > div > div > input:focus, 
    .stSelectbox > div > div > div:focus, 
    .stTextArea > div > div > textarea:focus {
        border-color: #000000 !important;
        box-shadow: none !important;
    }
    
    /* Box del Form senza ombre pesanti, solo un bordo sottile */
    [data-testid="stForm"] {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
    
    /* Tab di navigazione semplici */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #e5e7eb;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 16px;
        background-color: transparent;
        font-size: 1rem;
        font-weight: 500;
        color: #6b7280;
    }
    .stTabs [aria-selected="true"] {
        color: #000000 !important;
        border-bottom: 2px solid #000000 !important;
    }
    
    /* Rimozione decorazioni superflue */
    hr {
        border-color: #e5e7eb !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. GESTIONE DATABASE LOCALE
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

# Gestione dello stato della sessione
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
# 2. GENERAZIONE SCHEDA PDF (Semplificata)
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
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#000000'), spaceAfter=10)
    h2_style = ParagraphStyle('SectionH2', parent=styles['Heading2'], fontSize=13, leading=16, textColor=colors.HexColor('#111827'), spaceBefore=12, spaceAfter=6)
    h3_style = ParagraphStyle('SectionH3', parent=styles['Heading3'], fontSize=11, leading=14, textColor=colors.HexColor('#374151'), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#111827'), spaceAfter=4)

    story = []
    story.append(Paragraph("<b>BASKETBALL COACH PRO - PROGRAMMA DI ALLENAMENTO</b>", title_style))
    story.append(Paragraph(f"<b>Atleta:</b> {html.escape(nome_utente)}", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#000000'), spaceBefore=6, spaceAfter=12))
    
    righe = testo_scheda.split('\n')
    for riga in righe:
        riga_str = riga.strip()
        if not riga_str:
            story.append(Spacer(1, 4))
            continue
            
        if riga_str.startswith('### '):
            story.append(Paragraph(pulisci_e_formatta_testo_pdf(riga_str.replace('### ', '')), h3_style))
        elif riga_str.startswith('## '):
            story.append(Paragraph(pulisci_e_formatta_testo_pdf(riga_str.replace('## ', '')), h2_style))
        elif riga_str.startswith('# '):
            story.append(Paragraph(pulisci_e_formatta_testo_pdf(riga_str.replace('# ', '')), title_style))
        elif riga_str.startswith('---'):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.gray, spaceBefore=6, spaceAfter=6))
        else:
            story.append(Paragraph(pulisci_e_formatta_testo_pdf(riga_str), body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================================
# 3. SCHERMATA LOGIN / REGISTRAZIONE
# ==========================================
if not st.session_state['logged_in']:
    st.title("Basketball Coach PRO")
    st.write("Accedi o crea un account per generare i tuoi programmi di allenamento.")
    
    st.markdown("<br>", unsafe_allow_html=True)
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
                st.success(f"Bentornato {user_data[0]}")
                st.rerun()
            else:
                st.error("Username o Password errati.")

    with tab_register:
        reg_user = st.text_input("Scegli un Username")
        reg_email = st.text_input("Email")
        reg_pass = st.text_input("Scegli una Password", type="password")
        if st.button("Crea Account"):
            if reg_user and reg_pass:
                if crea_utente(reg_user, reg_pass, reg_email):
                    st.success("Account creato con successo. Ora puoi accedere.")
                else:
                    st.error("Username già in uso. Scegline un altro.")
            else:
                st.warning("Inserisci Username e Password validi.")

# ==========================================
# 4. APP PRINCIPALE
# ==========================================
else:
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title(f"Area Atleta: {st.session_state['username']}")
    with col_head2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Esci (Logout)"):
            st.session_state['logged_in'] = False
            st.session_state['scheda_generata'] = ''
            st.rerun()

    if "GROQ_API_KEY" in st.secrets:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    else:
        st.error("Chiave API non trovata nei Secrets di Streamlit.")
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
            return "Nessun esercizio specifico estratto dal web, procedi con la tua conoscenza delle metodologie dei Preparatori Atletici d'élite."
        return "Conferma ispirazione web:\n" + "\n".join([f"- {t}" for t in video_found])

    main_tab1, main_tab2 = st.tabs(["Prepara Nuova Scheda", "Archivio Schede"])

    with main_tab1:
        st.write("Compila i campi per ricevere un programma settimanale rigoroso e strutturato sui tuoi dati.")

        with st.form("coach_form"):
            st.markdown("### Dati e Organizzazione")
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome dell'atleta", value=st.session_state['username'])
                eta = st.number_input("Età", min_value=5, max_value=60, value=18)
                ruolo = st.selectbox("Ruolo in campo", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
                livello = st.selectbox("Livello attuale", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
            with col2:
                obiettivo = st.text_input("Obiettivo (es. primo passo, tiro, letture)")
                frequenza = st.selectbox("Giorni di allenamento a settimana", ["1-2 volte", "3-4 volte", "5+ volte"])
                durata_singola = st.selectbox("Durata della singola sessione", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
                logistica = st.selectbox("Modalità", ["Da solo", "In compagnia"])

            st.markdown("### Condizioni e Ispirazione")
            col3, col4 = st.columns(2)
            with col3:
                giocatori_simili = st.text_input("Giocatori a cui ti ispiri", value=st.session_state['giocatori_memoria'])
            with col4:
                note_extra = st.text_area("Infortuni o limitazioni? (Es: fastidio al ginocchio, 1 solo pallone)")
            
            submit_button = st.form_submit_button(label="Genera Programma")

        if submit_button:
            aggiorna_memoria_giocatori(st.session_state['username'], giocatori_simili)
            st.session_state['giocatori_memoria'] = giocatori_simili
            st.session_state['nome_atleta_scheda'] = nome

            num_giorni = 2
            if "3-4" in frequenza: num_giorni = 4
            elif "5+" in frequenza: num_giorni = 5

            with st.spinner("Elaborazione del programma in corso..."):
                risultati_youtube = cerca_video_youtube_dettagliati(giocatori_simili, obiettivo)

            progress_bar = st.progress(0)
            status_text = st.empty()

            scheda_completa = f"# PROGRAMMAZIONE SETTIMANALE - {nome.upper()}\n"
            scheda_completa += f"**Ruolo:** {ruolo} | **Livello:** {livello} | **Età:** {eta} anni | **Obiettivo:** {obiettivo}\n"
            scheda_completa += f"**Frequenza:** {frequenza} ({num_giorni} giorni) | **Durata Sessione:** {durata_singola} | **Modalità:** {logistica}\n"
            scheda_completa += f"**Condizioni Fisiche/Logistiche:** {note_extra}\n"
            scheda_completa += f"**Ispirazione:** {giocatori_simili}\n\n---\n\n"

            try:
                for giorno_idx in range(1, num_giorni + 1):
                    status_text.text(f"Elaborazione Giorno {giorno_idx} di {num_giorni}...")
                    
                    esercizi_gia_inseriti = scheda_completa[-2500:] if giorno_idx > 1 else "Nessun esercizio precedente."

                    prompt_giorno = f"""
                    Agisci come un Head Coach e Preparatore Atletico professionista di basket.
                    NON MENZIONARE MAI DI ESSERE UN'IA, UN PROGRAMMA, O UN MODELLO LINGUISTICO. PARLA E SCRIVI DIRETTAMENTE COME UN COACH UMANO. NESSUN SALUTO INIZIALE TIPO "CIAO" O "ECCO LA SCHEDA", VAI DRITTO AL PIANO.

                    Struttura il **GIORNO {giorno_idx}** del programma.
                    
                    DATI DELL'ATLETA DA RISPETTARE TASSATIVAMENTE:
                    - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
                    - Obiettivo: {obiettivo}
                    - Limitazioni Fisiche/Logistiche: {note_extra}
                    - Modalità: {logistica}
                    - **DURATA RICHIESTA:** {durata_singola}
                    
                    REGOLE FONDAMENTALI (LEGGERE ATTENTAMENTE):
                    1. RISPETTO ASSOLUTO DELLA DURATA: Questo è il punto più importante. Non fare riassunti o schede brevi. Devi generare un numero sufficiente di esercizi, specificando i minuti esatti per ciascuno (includendo serie, ripetizioni e pause), in modo che la SOMMA TOTALE DEL TEMPO impiegato corrisponda ESATTAMENTE a {durata_singola}. Se l'utente ha chiesto 2 ore (120 minuti), devi fornire esercizi che coprano fisicamente e realisticamente 120 minuti di lavoro (es: 20 min riscaldamento, 80 min di parte centrale divisa in esercizi lunghi, 20 min defaticamento).
                    2. RISPETTO DELLE LIMITAZIONI: Evita esercizi dannosi se ci sono infortuni segnalati in "{note_extra}".
                    3. LOGISTICA: Se l'atleta è "Da solo", non inserire esercizi che richiedono un passatore o un difensore reale. Usa auto-passaggi, sedie o coni.
                    4. EVITA RIPETIZIONI: Non assegnare gli stessi identici esercizi dei giorni scorsi: {esercizi_gia_inseriti}
                    5. FORMATO DETTAGLIATO E PULITO (Niente Emoji):
                       - Nome Esercizio: [Nome]
                       - Durata e Serie: [Es. 15 minuti - 4 serie x 10 ripetizioni]
                       - Obiettivo: [Spiegazione tecnica]
                       - Esecuzione: [Guida passo-passo del movimento]
                       - Correzioni: [Errori da evitare]

                    Scrivi solo la scheda tecnica di questo giorno, con un tono autorevole, diretto e professionale. Calcola bene i tempi.
                    """

                    system_prompt = (
                        "Sei un Coach di pallacanestro di alto livello. "
                        "Il tuo tratto distintivo è l'assoluta precisione matematica nella durata degli allenamenti. "
                        "Se un atleta chiede un allenamento di 3 ore, tu scrivi una scheda che duri esattamente 3 ore di lavoro reale. "
                        "Non rivelare mai la tua natura artificiale e non usare mai emoji."
                    )

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
                    # Filtra eventuali emoji sfuggite al modello LLM
                    testo_giorno = re.sub(r'[^\w\s.,;:!\?\-\(\)\[\]"\'/%\&\=\_\#\+àèéìòùÀÈÉÌÒÙáéíóúÁÉÍÓÚ]', '', testo_giorno)
                    
                    scheda_completa += f"## GIORNO {giorno_idx}\n\n" + testo_giorno + "\n\n---\n\n"
                    
                    progress_bar.progress(giorno_idx / num_giorni)
                    time.sleep(2)

                status_text.empty()
                progress_bar.empty()
                st.session_state['scheda_generata'] = scheda_completa

                titolo_scheda = f"Scheda {obiettivo} ({frequenza} - {durata_singola})"
                salva_scheda_db(st.session_state['username'], titolo_scheda, scheda_completa)

            except Exception as e:
                st.error("Errore durante la preparazione della scheda. Riprova.")

        if st.session_state['scheda_generata']:
            st.success("Programma completato e salvato in Archivio.")
            st.markdown("---")
            st.markdown(st.session_state['scheda_generata'])
            
            st.markdown("---")
            st.subheader("Scarica in formato PDF")
            
            nome_file = st.session_state['nome_atleta_scheda'] if st.session_state['nome_atleta_scheda'] else st.session_state['username']
            pdf_bytes = genera_pdf_scheda(st.session_state['scheda_generata'], nome_file)
            
            st.download_button(
                label="Scarica Scheda PDF",
                data=pdf_bytes,
                file_name=f"Scheda_Basketball_{nome_file.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

    with main_tab2:
        st.write("Consulta o scarica le schede salvate in precedenza.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        schede_salvate = get_schede_utente_db(st.session_state['username'])
        
        if not schede_salvate:
            st.info("Nessuna scheda presente in archivio.")
        else:
            opzioni_schede = {f"{s[1]} - {s[2]}": s for s in schede_salvate}
            scheda_selezionata_label = st.selectbox("Seleziona una scheda dall'archivio:", list(opzioni_schede.keys()))
            
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
                    st.success("Scheda eliminata dall'archivio.")
                    st.rerun()
            
            st.markdown("---")
            st.markdown(scheda_testo)
