code_content = '''import streamlit as st
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
    c.execute(\'''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            email TEXT,
            giocatori_salvati TEXT
        )
    \''')
    c.execute(\'''
        CREATE TABLE IF NOT EXISTS schede (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            data_creazione TEXT NOT NULL,
            titolo TEXT NOT NULL,
            contenuto TEXT NOT NULL
        )
    \''')
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
# 2. FUNZIONE GENERAZIONE PDF
# ==========================================
def pulisci_e_formatta_testo_pdf(testo):
    testo_pulito = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF\s\.,;:!\?\-\(\)\[\]"\'/%\&\=\_\#\+]', '', testo)
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
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#ea580c'), spaceAfter=10)
    h2_style = ParagraphStyle('SectionH2', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#1a202c'), spaceBefore=12, spaceAfter=6)
    h3_style = ParagraphStyle('SectionH3', parent=styles['Heading3'], fontSize=12, leading=16, textColor=colors.HexColor('#c2410c'), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#334155'), spaceAfter=4)

    story = []
    story.append(Paragraph("<b>BASKETBALL COACH PRO - SCHEDA UFFICIALE</b>", title_style))
    story.append(Paragraph(f"<b>Atleta:</b> {html.escape(nome_utente)}", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#ea580c'), spaceBefore=6, spaceAfter=12))
    
    righe = testo_scheda.split('\\n')
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
# 3. SCHERMATA DI LOGIN / REGISTRAZIONE
# ==========================================
if not st.session_state['logged_in']:
    st.title("🏀 Basketball Coach PRO")
    st.write("Accedi o crea un account per generare e salvare i tuoi programmi di allenamento personalizzati.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    tab_login, tab_register = st.tabs(["🔑 Accedi", "📝 Registrati (Nuovo Account)"])
    
    with tab_login:
        st.markdown("### Fai il Login")
        log_user = st.text_input("Username", key="log_user")
        log_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Accedi al tuo Profilo"):
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
        st.markdown("### Crea il tuo profilo unico")
        reg_user = st.text_input("Scegli un Username Unico")
        reg_email = st.text_input("Email")
        reg_pass = st.text_input("Scegli una Password", type="password")
        if st.button("Crea Account"):
            if reg_user and reg_pass:
                if crea_utente(reg_user, reg_pass, reg_email):
                    st.success("Account creato con successo! Ora puoi fare il login nella sezione 'Accedi'.")
                else:
                    st.error("⚠️ Questo Username è già in uso! Scegline un altro.")
            else:
                st.warning("Inserisci Username e Password validi.")

# ==========================================
# 4. APP PRINCIPALE (Accessibile solo se loggati)
# ==========================================
else:
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.title(f"🏀 Profilo Atleta: {st.session_state['username']}")
    with col_head2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Esci (Logout)"):
            st.session_state['logged_in'] = False
            st.session_state['scheda_generata'] = ''
            st.rerun()

    if "GROQ_API_KEY" in st.secrets:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    else:
        st.error("⚠️ Chiave API non trovata nei Secrets di Streamlit!")
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
            return "Nessun esercizio specifico estratto dal web, procedi con la profonda conoscenza delle metodologie dei Master Coach e dei Preparatori Atletici d'élite."
        return "Esercizi, concetti chiave e metodologie d'élite individuati per ispirazione dal web:\\n" + "\\n".join([f"- {t}" for t in video_found])

    main_tab1, main_tab2 = st.tabs(["➕ Genera Nuova Scheda", "📂 Archivio Schede"])

    with main_tab1:
        st.markdown("""
        <p style='font-size: 1.1rem; color: #475569;'>
        Crea il tuo programma settimanale strutturato. Il sistema genera la tua scheda unendo i tuoi dati personali con i protocolli tattici e fisici dei migliori allenatori e preparatori al mondo.
        </p>
        """, unsafe_allow_html=True)

        with st.form("coach_form"):
            st.markdown("### 📋 1. Dati Atleta e Organizzazione")
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome dell'atleta", value=st.session_state['username'])
                eta = st.number_input("Età", min_value=5, max_value=60, value=18)
                ruolo = st.selectbox("Ruolo principale in campo", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
                livello = st.selectbox("Livello attuale", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
            with col2:
                obiettivo = st.text_input("Cosa vuoi migliorare? (es. primo passo, tiro dal palleggio, letture)")
                frequenza = st.selectbox("Giorni di allenamento a settimana", ["1-2 volte", "3-4 volte", "5+ volte"])
                durata_singola = st.selectbox("Durata della singola sessione", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
                logistica = st.selectbox("Con chi ti alleni?", ["Da solo", "In compagnia (con compagni)"])

            st.markdown("### 🏥 2. Salute & Ispirazione")
            col3, col4 = st.columns(2)
            with col3:
                giocatori_simili = st.text_input("Giocatori a cui ti ispiri (es. Steph Curry, LeBron James)", value=st.session_state['giocatori_memoria'])
            with col4:
                note_extra = st.text_area("Infortuni attuali o attrezzatura limitata? (Es: Dolore al ginocchio, Ho solo un pallone)")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button(label="🏀 CREA IL MIO PROGRAMMA DI ALLENAMENTO")

        if submit_button:
            aggiorna_memoria_giocatori(st.session_state['username'], giocatori_simili)
            st.session_state['giocatori_memoria'] = giocatori_simili
            st.session_state['nome_atleta_scheda'] = nome

            num_giorni = 2
            if "3-4" in frequenza: num_giorni = 4
            elif "5+" in frequenza: num_giorni = 5

            with st.spinner("Creazione del programma in corso... elaborazione delle metodologie tattiche e fisiche..."):
                risultati_youtube = cerca_video_youtube_dettagliati(giocatori_simili, obiettivo)

            progress_bar = st.progress(0)
            status_text = st.empty()

            scheda_completa = f"# 🏀 PROGRAMMAZIONE SETTIMANALE - {nome.upper()}\\n"
            scheda_completa += f"**Ruolo:** {ruolo} | **Livello:** {livello} | **Età:** {eta} anni | **Obiettivo:** {obiettivo}\\n"
            scheda_completa += f"**Frequenza:** {frequenza} ({num_giorni} giorni di lavoro) | **Durata Sessione:** {durata_singola} | **Modalità:** {logistica}\\n"
            scheda_completa += f"**Condizioni Fisiche/Logistiche:** {note_extra}\\n"
            scheda_completa += f"**Ispirazione:** {giocatori_simili}\\n\\n---\\n\\n"

            try:
                for giorno_idx in range(1, num_giorni + 1):
                    status_text.text(f"⏳ Strutturazione Giorno {giorno_idx} di {num_giorni}...")
                    
                    esercizi_gia_inseriti = scheda_completa[-2500:] if giorno_idx > 1 else "Nessun esercizio precedente."

                    prompt_giorno = f"""
                    Agisci come il più grande Head Coach e Preparatore Atletico del mondo.
                    Hai integrato le conoscenze di leggende come Phil Jackson, Gregg Popovich, Steve Kerr, Pat Riley, Paul Fabritz, Tim Grover, ecc.
                    NON MENZIONARE MAI DI ESSERE UN'IA, UN PROGRAMMA, O UN MODELLO LINGUISTICO. PARLA DIRETTAMENTE COME UN COACH UMANO ESPERTO E DIRETTO.

                    Struttura il **GIORNO {giorno_idx}** di un programma di {num_giorni} giorni totali.
                    DATI DELL'ATLETA DA RISPETTARE TASSATIVAMENTE:
                    - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
                    - OBIETTIVO: {obiettivo}
                    - INFORTUNI / ATTREZZI LIMITATI: {note_extra}
                    - DURATA SESSIONE: {durata_singola} | MODALITÀ: {logistica}
                    
                    REGOLE:
                    1. RISCALDAMENTO/DEFATICAMENTO: Attivazione neuromuscolare moderna all'inizio, decompressione alla fine. Adatta all'età ({eta} anni) e agli infortuni ({note_extra}).
                    2. PARTE CENTRALE: Esercizi a game-speed basati sulle filosofie dei grandi coach. Usa auto-passaggi se l'atleta è "Da solo".
                    3. NESSUN COMPAGNO SE "DA SOLO": Rispetta la logistica.
                    4. EVITA RIPETIZIONI: Ecco cosa hai già assegnato nei giorni scorsi (non ripetere): {esercizi_gia_inseriti}
                    5. FORMATO DETTAGLIATO:
                       - **Nome Esercizio:** [Nome chiaro]
                       - **Serie & Durata:** [Es. 3 serie x 10 rep]
                       - **🎯 Obiettivo:** [Perché serve questo esercizio, considerando età e infortuni]
                       - **📖 Esecuzione:** [Guida passo-passo sui movimenti e postura]
                       - **⚠️ Correzioni:** [2 errori comuni da non fare]

                    Scrivi solo il piano di allenamento con un tono motivante, autorevole e professionale. Non inserire link web.
                    """

                    system_prompt = (
                        "Sei il Coach di pallacanestro definitivo. Strutturi programmi di allenamento perfetti unendo la tattica dei migliori Head Coach e la scienza dei migliori Preparatori Atletici. "
                        "Non rivelare MAI la tua natura artificiale (es. non dire 'sono un'IA' o 'come intelligenza artificiale'). Comportati e scrivi come un professionista reale del basket. "
                        "Presta assoluta attenzione all'età dell'atleta e alle sue condizioni fisiche."
                    )

                    chat_completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt_giorno}
                        ],
                        temperature=0.25,
                        max_tokens=2200
                    )

                    testo_giorno = chat_completion.choices[0].message.content
                    scheda_completa += f"## 📅 GIORNO {giorno_idx}\\n\\n" + testo_giorno + "\\n\\n---\\n\\n"
                    
                    progress_bar.progress(giorno_idx / num_giorni)
                    time.sleep(2.5)

                status_text.empty()
                progress_bar.empty()
                st.session_state['scheda_generata'] = scheda_completa

                titolo_scheda = f"Scheda {obiettivo} ({frequenza} - {durata_singola})"
                salva_scheda_db(st.session_state['username'], titolo_scheda, scheda_completa)

            except Exception as e:
                st.error("Si è verificato un errore durante la creazione del programma. Riprova.")

        if st.session_state['scheda_generata']:
            st.success("✅ Programma completato e salvato in Archivio!")
            st.markdown("---")
            st.markdown(st.session_state['scheda_generata'])
            
            st.markdown("---")
            st.subheader("📄 Scarica il tuo PDF")
            
            nome_file = st.session_state['nome_atleta_scheda'] if st.session_state['nome_atleta_scheda'] else st.session_state['username']
            pdf_bytes = genera_pdf_scheda(st.session_state['scheda_generata'], nome_file)
            
            st.download_button(
                label="📥 Scarica Scheda in formato PDF",
                data=pdf_bytes,
                file_name=f"Scheda_Basketball_{nome_file.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

    with main_tab2:
        st.markdown("### 📂 Le tue Schede Salvate")
        st.write("Qui trovi lo storico dei tuoi allenamenti. Rileggi, scarica o elimina le schede passate.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        schede_salvate = get_schede_utente_db(st.session_state['username'])
        
        if not schede_salvate:
            st.info("ℹ️ Non hai ancora nessuna scheda salvata nel tuo archivio. Torna alla sezione 'Genera Nuova Scheda' per iniziare!")
        else:
            opzioni_schede = {f"📅 {s[1]} - {s[2]}": s for s in schede_salvate}
            scheda_selezionata_label = st.selectbox("Seleziona una scheda salvata:", list(opzioni_schede.keys()))
            
            scheda_dati = opzioni_schede[scheda_selezionata_label]
            scheda_id = scheda_dati[0]
            scheda_data = scheda_dati[1]
            scheda_titolo = scheda_dati[2]
            scheda_testo = scheda_dati[3]
            
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                pdf_salvato = genera_pdf_scheda(scheda_testo, st.session_state['username'])
                st.download_button(
                    label="📥 Scarica PDF di questa scheda",
                    data=pdf_salvato,
                    file_name=f"Scheda_{st.session_state['username']}_{scheda_id}.pdf",
                    mime="application/pdf",
                    key=f"dl_{scheda_id}"
                )
            with col_btn2:
                if st.button("🗑️ Elimina", key=f"del_{scheda_id}"):
                    elimina_scheda_db(scheda_id)
                    st.success("Scheda eliminata dall'archivio!")
                    st.rerun()
            
            st.markdown("---")
            st.markdown(scheda_testo)
'''

with open('app_web.py', 'w', encoding='utf-8') as f:
    f.write(code_content)
