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

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach PRO", page_icon="🏀", layout="wide")

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
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#1E3A8A'), spaceAfter=10)
    h2_style = ParagraphStyle('SectionH2', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#1E3A8A'), spaceBefore=12, spaceAfter=6)
    h3_style = ParagraphStyle('SectionH3', parent=styles['Heading3'], fontSize=12, leading=16, textColor=colors.HexColor('#2563EB'), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#1F2937'), spaceAfter=4)

    story = []
    story.append(Paragraph("<b>AI BASKETBALL COACH PRO - SCHEDA UFFICIALE</b>", title_style))
    story.append(Paragraph(f"<b>Atleta:</b> {html.escape(nome_utente)}", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceBefore=6, spaceAfter=12))
    
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
# 3. SCHERMATA DI LOGIN / REGISTRAZIONE
# ==========================================
if not st.session_state['logged_in']:
    st.title("🏀 Benvenuto in AI Basketball Coach PRO")
    st.write("Accedi o crea un account per iniziare il tuo percorso e salvare le tue preferenze.")
    
    tab_login, tab_register = st.tabs(["🔑 Accedi", "📝 Registrati (Nuovo Account)"])
    
    with tab_login:
        st.subheader("Fai il Login")
        log_user = st.text_input("Username", key="log_user")
        log_pass = st.text_input("Password", type="password", key="log_pass")
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
        if st.button("Crea Account"):
            if reg_user and reg_pass:
                if crea_utente(reg_user, reg_pass, reg_email):
                    st.success("Account creato con successo! Ora puoi fare il login.")
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
        st.title(f"🏀 AI Basketball Coach PRO - Profilo di {st.session_state['username']}")
    with col_head2:
        if st.button("🚪 Logout"):
            st.session_state['logged_in'] = False
            st.session_state['scheda_generata'] = ''
            st.rerun()

    if "GROQ_API_KEY" in st.secrets:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    else:
        st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
        st.stop()

    client = Groq(api_key=groq_api_key)

    def cerca_video_youtube_dettagliati(giocatori, obiettivo):
        video_found = []
        queries = []
        lista_g = [g.strip() for g in giocatori.split(',') if g.strip()]
        for g in lista_g:
            queries.append(f"{g} basketball drill breakdown")
            queries.append(f"{g} basketball workout tutorial")
        if obiettivo:
            queries.append(f"best basketball {obiettivo} drill tutorial")

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
            return "Nessun esercizio specifico estratto dal web, procedi con la tua conoscenza di Master Coach."
        return "Esercizi e concetti chiave individuati per ispirazione dal web:\n" + "\n".join([f"- {t}" for t in video_found])

    main_tab1, main_tab2 = st.tabs(["➕ Genera Nuova Scheda", "📂 Archivio Schede Salvate"])

    with main_tab1:
        st.write("Programmazione settimanale Elite con spiegazioni iper-dettagliate passo-passo e adattamento logistico perfetto.")

        with st.form("coach_form"):
            st.subheader("Parametri del Giocatore e Programmazione")
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome del giocatore", value=st.session_state['username'])
                eta = st.number_input("Età", min_value=5, max_value=60, value=18)
                ruolo = st.selectbox("Ruolo principale", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
                livello = st.selectbox("Livello di gioco", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
            with col2:
                obiettivo = st.text_input("Obiettivo preciso (es. primo passo esplosivo, handles, tiro dal palleggio)")
                frequenza = st.selectbox("Frequenza settimanale", ["1-2 volte", "3-4 volte", "5+ volte"])
                durata_singola = st.radio("Durata esatta singola sessione:", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
                logistica = st.radio("Logistica di allenamento:", ["Da solo", "In compagnia"])

            st.subheader("Film Study & Giocatori Modello")
            giocatori_simili = st.text_input("A chi ti ispiri? (Separa con virgola. Es: Stephen Curry, Kobe Bryant)", value=st.session_state['giocatori_memoria'])
            note_extra = st.text_area("Note (es. infortuni, attrezzi a disposizione come coni, pallina da tennis)")
            
            submit_button = st.form_submit_button(label="Genera Scheda di Allenamento Elite")

        if submit_button:
            aggiorna_memoria_giocatori(st.session_state['username'], giocatori_simili)
            st.session_state['giocatori_memoria'] = giocatori_simili
            st.session_state['nome_atleta_scheda'] = nome

            num_giorni = 2
            if "3-4" in frequenza: num_giorni = 4
            elif "5+" in frequenza: num_giorni = 5

            with st.spinner("Scansione dei database dei professionisti e dei migliori esercizi sul web..."):
                risultati_youtube = cerca_video_youtube_dettagliati(giocatori_simili, obiettivo)

            progress_bar = st.progress(0)
            status_text = st.empty()

            scheda_completa = f"# 🏀 PROGRAMMAZIONE SETTIMANALE ELITE - {nome.upper()}\n"
            scheda_completa += f"**Ruolo:** {ruolo} | **Livello:** {livello} | **Obiettivo:** {obiettivo}\n"
            scheda_completa += f"**Frequenza:** {frequenza} ({num_giorni} giorni di lavoro) | **Durata Sessione:** {durata_singola} | **Modalità:** {logistica}\n"
            scheda_completa += f"**Ispirazione:** {giocatori_simili}\n\n---\n\n"

            try:
                for giorno_idx in range(1, num_giorni + 1):
                    status_text.text(f"⏳ Elaborazione analitica Giorno {giorno_idx} di {num_giorni}: massimizzazione dei dettagli e controllo ripetizioni...")
                    
                    # Memoria dinamica per non ripetere MAI gli stessi esercizi (prende l'ultima porzione cospicua di testo generato)
                    esercizi_gia_inseriti = scheda_completa[-2500:] if giorno_idx > 1 else "Ancora nessun esercizio assegnato."

                    prompt_giorno = f"""
                    Agisci come un Master Coach e Preparatore Atletico NBA di livello mondiale.
                    Il tuo compito è strutturare il **GIORNO {giorno_idx}** di un programma di allenamento d'élite di {num_giorni} giorni totali.

                    DATI DELL'ATLETA DA ANALIZZARE RIGOROSAMENTE:
                    - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
                    - OBIETTIVO PRINCIPALE: {obiettivo}
                    - DURATA SESSIONE: {durata_singola}
                    - LOGISTICA DI ALLENAMENTO: {logistica}
                    - NOTE E ATTREZZI: {note_extra}
                    - ISPIRAZIONE (Giocatori Modello): {giocatori_simili}
                    - SPUNTI DAL WEB E DAI PRO: {risultati_youtube}

                    ISTRUZIONI DI COMPOSIZIONE:
                    1. ADATTAMENTO LOGISTICO ASSOLUTO: Valuta la logistica richiesta. Se l'utente ha selezionato 'Da solo', NON INSERIRE MAI esercizi che richiedano un compagno, un passatore o un difensore. Ogni drill deve essere 100% eseguibile in solitaria, usando magari tabellone o auto-passaggi se necessario.
                    
                    2. SELEZIONE ESERCIZI D'ÉLITE E ZERO RIPETIZIONI: Scegli solo gli esercizi più efficaci e moderni. NON ripetere MAI esercizi o varianti banali degli esercizi già assegnati nei giorni precedenti. Varia gli angoli, gli stimoli e la tipologia di lavoro.
                       Ecco gli esercizi già assegnati nei giorni precedenti (NON REPLICARLI):
                       {esercizi_gia_inseriti}

                    3. STRUTTURA DELLA SESSIONE: Dividi fluidamente il GIORNO {giorno_idx} in: Riscaldamento & Mobilità, Blocco Tecnico & Signature Drills, Blocco Situazionale & Tiro, Defaticamento & Flex.

                    4. SPIEGAZIONE IPER-DETTAGLIATA (FORMATO OBBLIGATORIO):
                       Per garantire all'atleta la massima comprensione, per OGNI SINGOLO ESERCIZIO (inclusi riscaldamento e defaticamento) devi usare ESATTAMENTE questo formato:
                       - **Nome Esercizio:** [Nome chiaro e professionale]
                       - **Durata & Serie:** [Serie | Reps o Tempo | Recupero]
                       - **🎯 Obiettivo Specifico:** [Analisi tecnica e biomeccanica di cosa si sta migliorando]
                       - **📖 Esecuzione Passo-Passo:** [Guida estrema: descrivi la postura iniziale, il lavoro esatto dei piedi (footwork), l'uso del baricentro, la posizione delle mani e la gestione del pallone]
                       - **⚠️ Errori Comuni da Evitare:** [Indica i 2 errori tecnici, posturali o di timing più frequenti e come correggerli]

                    IMPORTANTE: Non includere mai link, URL o riferimenti a YouTube nel testo finale.
                    """

                    chat_completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": "Sei un Master Coach NBA. Genera le schede analizzando con assoluto rigore i parametri logistici e garantendo spiegazioni biomeccaniche iper-dettagliate senza mai ripetere esercizi."},
                            {"role": "user", "content": prompt_giorno}
                        ],
                        temperature=0.25,
                        max_tokens=2200
                    )

                    testo_giorno = chat_completion.choices[0].message.content
                    scheda_completa += f"## 📅 GIORNO {giorno_idx}\n\n" + testo_giorno + "\n\n---\n\n"
                    
                    progress_bar.progress(giorno_idx / num_giorni)
                    time.sleep(2.5) # Pausa di sicurezza estesa a 2.5 secondi per garantire di evitare per sempre l'errore 413/429

                status_text.empty()
                progress_bar.empty()
                st.session_state['scheda_generata'] = scheda_completa

                titolo_scheda = f"Scheda {obiettivo} ({frequenza} - {durata_singola})"
                salva_scheda_db(st.session_state['username'], titolo_scheda, scheda_completa)

            except Exception as e:
                st.error(f"Si è verificato un errore durante la generazione: {e}")

        if st.session_state['scheda_generata']:
            st.success("Programmazione Settimanale Completa Generata e Salvata in Archivio!")
            st.markdown("---")
            st.markdown(st.session_state['scheda_generata'])
            
            st.markdown("---")
            st.subheader("📄 Scarica la tua Scheda Ufficiale in PDF")
            
            nome_file = st.session_state['nome_atleta_scheda'] if st.session_state['nome_atleta_scheda'] else st.session_state['username']
            pdf_bytes = genera_pdf_scheda(st.session_state['scheda_generata'], nome_file)
            
            st.download_button(
                label="📥 Scarica Scheda Completa in PDF",
                data=pdf_bytes,
                file_name=f"Scheda_Basketball_{nome_file.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

    with main_tab2:
        st.subheader("📂 Il tuo Archivio Personalizzato di Schede Salvate")
        st.write("Qui trovi tutte le schede generate precedentemente. Puoi rileggerle, scaricare i relativi PDF o eliminarle.")
        
        schede_salvate = get_schede_utente_db(st.session_state['username'])
        
        if not schede_salvate:
            st.info("ℹ️ Non hai ancora nessuna scheda salvata nel tuo archivio. Generane una dalla scheda 'Genera Nuova Scheda'!")
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
                if st.button("🗑️ Elimina Scheda", key=f"del_{scheda_id}"):
                    elimina_scheda_db(scheda_id)
                    st.success("Scheda eliminata con successo dall'archivio!")
                    st.rerun()
            
            st.markdown("---")
            st.markdown(scheda_testo)
