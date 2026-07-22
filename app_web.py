import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch
import sqlite3
import hashlib
import io
import re
import html
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
if 'scheda_generata' not in st.session_state:
    st.session_state['scheda_generata'] = ''
if 'nome_atleta_scheda' not in st.session_state:
    st.session_state['nome_atleta_scheda'] = ''

# ==========================================
# 2. FUNZIONE GENERAZIONE PDF
# ==========================================
def pulisci_e_formatta_testo_pdf(testo):
    # Rimuove emoji incompatibili coi font PDF standard
    testo_pulito = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF\s\.,;:!\?\-\(\)\[\]"\'/%\&\=\_\#\+]', '', testo)
    # Protegge caratteri speciali XML
    testo_escaped = html.escape(testo_pulito)
    # Converte il grassetto e corsivo Markdown per ReportLab
    testo_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', testo_escaped)
    testo_formatted = re.sub(r'\*(.*?)\*', r'<i>\1</i>', testo_formatted)
    return testo_formatted

def genera_pdf_scheda(testo_scheda, nome_utente):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=10
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=12,
        spaceAfter=6
    )

    h3_style = ParagraphStyle(
        'SectionH3',
        parent=styles['Heading3'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=10,
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=4
    )

    story = []
    
    # Intestazione Documento PDF
    story.append(Paragraph("<b>AI BASKETBALL COACH PRO - SCHEDA UFFICIALE</b>", title_style))
    story.append(Paragraph(f"<b>Atleta:</b> {html.escape(nome_utente)}", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceBefore=6, spaceAfter=12))
    
    # Processa il testo riga per riga
    righe = testo_scheda.split('\n')
    for riga in righe:
        riga_str = riga.strip()
        if not riga_str:
            story.append(Spacer(1, 4))
            continue
            
        if riga_str.startswith('### '):
            testo_f = pulisci_e_formatta_testo_pdf(riga_str.replace('### ', ''))
            story.append(Paragraph(testo_f, h3_style))
        elif riga_str.startswith('## '):
            testo_f = pulisci_e_formatta_testo_pdf(riga_str.replace('## ', ''))
            story.append(Paragraph(testo_f, h2_style))
        elif riga_str.startswith('# '):
            testo_f = pulisci_e_formatta_testo_pdf(riga_str.replace('# ', ''))
            story.append(Paragraph(testo_f, title_style))
        elif riga_str.startswith('---'):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.gray, spaceBefore=6, spaceAfter=6))
        else:
            testo_f = pulisci_e_formatta_testo_pdf(riga_str)
            story.append(Paragraph(testo_f, body_style))
            
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

    st.write("Programmazione settimanale Elite con calcolo rigoroso del volume.")

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
        aggiorna_memoria_giocatori(st.session_state['username'], giocatori_simili)
        st.session_state['giocatori_memoria'] = giocatori_simili
        st.session_state['nome_atleta_scheda'] = nome

        with st.spinner("Ricerca ed analisi dei video più popolari di basket su YouTube in corso..."):
            risultati_youtube = cerca_video_youtube_dettagliati(giocatori_simili, obiettivo)

        with st.spinner("L'IA sta costruendo la scheda completa per TUTTI i giorni richiesti..."):
            prompt = f"""
            Sei un MASTER COACH E PREPARATORE ATLETICO NBA DI LIVELLO MONDIALE.
            Il tuo compito è creare una programmazione settimanale completa, dove OGNI SINGOLO GIORNO ha lo STESSO IDENTICO livello di dettaglio profondo e rigoroso.

            DATI UTENTE TASSATIVI DA APPLICARE:
            - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
            - OBIETTIVO PRINCIPALE: {obiettivo}
            - FREQUENZA SETTIMANALE: {frequenza}  <-- CREA TUTTI I GIORNI PREVISTI!
            - DURATA SINGOLA SESSIONE: {durata_singola}
            - LOGISTICA: {logistica} (Se 'Da solo', VIETATI passaggi e difensori reali)
            - GIOCATORI MODELLO: {giocatori_simili}
            - NOTE/ATTREZZI: {note_extra}

            DATABASE VIDEO YOUTUBE VERIFICATI:
            {risultati_youtube}

            REGOLE RIGIDISSIME SULLA COMPLETEZZA DEI GIORNI:

            1. PARITÀ ASSOLUTA TRA I GIORNI (TASSATIVO):
               Sulla base della frequenza ({frequenza}), devi creare esplicitamente tutte le sezioni (es: "### GIORNO 1", "### GIORNO 2", "### GIORNO 3", "### GIORNO 4").
               È SEVERAMENTE VIETATO ridurre i dettagli, riassumere o saltare i campi dal Giorno 2 in poi.
               Il Giorno 2, il Giorno 3 e il Giorno 4 devono avere LA STESSA STRUTTURA E LO STESSO NUMERO DI ESERCIZI del Giorno 1. Non scrivere mai "ripeti il giorno 1" o "fai come sopra".

            2. VOLUME E DURATA ({durata_singola}):
               Ogni singolo giorno deve coprire {durata_singola}.
               - Se "2 ore" (120 min), inserisci per OGNI giorno almeno 7-8 esercizi completi divisi tra Riscaldamento, Blocco Signature Drills ({giocatori_simili}), Blocco Situazionale/Tiro ({obiettivo}) e Defaticamento.

            3. STRUTTURA TASSATIVA PER OGNI ESERCIZIO (IN TUTTI I GIORNI):
               Per OGNI esercizio di OGNI giorno devi compilare esattamente questi punti (sii denso, preciso ed essenziale senza fronzoli inutili):
               - **Nome Esercizio:** [Nome professionale]
               - **Durata & Serie:** [Serie | Reps/Tempo per lato | Recupero]
               - **🎯 Cosa allena nello specifico:** [Gesto tecnico/coordinativo preciso]
               - **⭐ Perché è stato scelto ("Best of the Best"):** [Motivazione in relazione a {obiettivo} e {giocatori_simili}]
               - **⚙️ Spiegazione Biomeccanica e Tecnica:** [Istruzioni su piedi, baricentro, postura e palla]
               - **🎥 Video di riferimento:** [Usa un URL esatto dal database + minutaggio. Es: https://www.youtube.com/watch?v=ID_VIDEO&t=90s (Guarda dal minuto 1:30)]
            """

            try:
                chat_completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Sei un Master Coach NBA. Mantieni il 100% di dettaglio, completezza e numero di esercizi per TUTTI i giorni della settimana, senza mai sintetizzare o tralasciare i giorni successivi al primo."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=8000
                )
                
                scheda = chat_completion.choices[0].message.content
                st.session_state['scheda_generata'] = scheda
                
            except Exception as e:
                st.error(f"Si è verificato un errore: {e}")

    # ==========================================
    # 5. VISUALIZZAZIONE SCHEDA E DOWNLOAD PDF
    # ==========================================
    if st.session_state['scheda_generata']:
        st.success("Programmazione Settimanale Elite generata con successo!")
        st.markdown("---")
        st.markdown(st.session_state['scheda_generata'])
        
        st.markdown("---")
        st.subheader("📄 Scarica la tua Scheda Ufficial in PDF")
        
        # Generazione PDF
        nome_file = st.session_state['nome_atleta_scheda'] if st.session_state['nome_atleta_scheda'] else st.session_state['username']
        pdf_bytes = genera_pdf_scheda(st.session_state['scheda_generata'], nome_file)
        
        st.download_button(
            label="📥 Scarica Scheda in PDF",
            data=pdf_bytes,
            file_name=f"Scheda_Basketball_{nome_file.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
