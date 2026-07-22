import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach PRO", page_icon="🏀", layout="wide")

st.title("🏀 AI Basketball Coach PRO")
st.write("Programmazione settimanale precisa al minuto con video ed esercizi con minutaggio (timestamp) diretto.")

# Controllo della chiave API nei Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
    st.stop()

client = Groq(api_key=groq_api_key)

# MOTORE DI RICERCA YOUTUBE PER SINGOLI DRILLS
def cerca_video_drills_specifici(giocatori, obiettivo):
    db_video_text = ""
    queries = []
    
    lista_g = [g.strip() for g in giocatori.split(',') if g.strip()]
    
    # Cerca drill specifici per ogni giocatore inserito
    for g in lista_g:
        queries.append(f"{g} signature basketball move drill tutorial")
        queries.append(f"{g} footwork breakdown")

    if obiettivo:
        queries.append(f"basketball {obiettivo} drill breakdown tutorial")

    for q in queries[:5]:
        try:
            search = VideosSearch(q, limit=2)
            results = search.result().get('result', [])
            for vid in results:
                v_id = vid.get('id')
                title = vid.get('title', 'Tutorial Esercizio').replace('[', '').replace(']', '').replace('"', '')
                if v_id:
                    clean_url = f"https://www.youtube.com/watch?v={v_id}"
                    thumb_url = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"
                    
                    db_video_text += f"""
- DRILL VIDEO: "{title}"
  ID: {v_id}
  URL BASE: {clean_url}
  IMG: {thumb_url}
  SINTASSI IMMAGINE: [![{title}]({thumb_url})]({clean_url})
"""
        except Exception:
            pass

    return db_video_text if db_video_text else "Nessun video trovato."


# INTERFACCIA UTENTE
with st.form("coach_form"):
    st.subheader("Parametri del Giocatore e Programmazione")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome del giocatore")
        eta = st.number_input("Età", min_value=5, max_value=60, value=18)
        ruolo = st.selectbox("Ruolo principale", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
        livello = st.selectbox("Livello di gioco", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
    
    with col2:
        obiettivo = st.text_input("Obiettivo preciso (es. primo passo esplosivo, handles/palleggio, tiro dal palleggio)")
        frequenza = st.selectbox("Frequenza settimanale", ["1-2 volte", "3-4 volte", "5+ volte"])
        durata_singola = st.radio("Durata esatta singola sessione:", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
        logistica = st.radio("Logistica di allenamento:", ["Da solo", "In compagnia"])

    st.subheader("Film Study & Giocatori Modello")
    giocatori_simili = st.text_input("A chi ti ispiri? (Separa con virgola. Es: Stephen Curry, Tyrese Maxey, Kyrie Irving)")
    note_extra = st.text_area("Note (es. infortuni, attrezzi a disposizione come coni, pallina da tennis, spara-palloni)")
    
    submit_button = st.form_submit_button(label="Genera Scheda Calibrata al Minuto")

# ELABORAZIONE
if submit_button:
    with st.spinner("Scansione database YouTube per trovare i singoli drill dei campioni..."):
        database_video_reali = cerca_video_drills_specifici(giocatori_simili, obiettivo)

    with st.spinner("L'IA sta calcolando il volume esatto degli esercizi per coprire l'intera durata richiesta..."):
        prompt = f"""
        Sei un MENTORE E PREPARATORE ATLETICO NBA di livello mondiale.
        Il tuo compito è creare un PROGRAMMA DI ALLENAMENTO SETTIMANALE iper-dettagliato, con gestione precisa del tempo ed esercizi legati a specifici minutaggi video.

        DATI UTENTE:
        - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
        - OBIETTIVO PRINCIPALE: {obiettivo}
        - FREQUENZA SETTIMANALE: {frequenza}
        - DURATA SINGOLA SESSIONE: {durata_singola}  <-- REGOLA CRUCIALE SUL TEMPO!
        - LOGISTICA: {logistica} (SE "DA SOLO": VIETATI PASSAGGI E DIFENSORI REALI)
        - GIOCATORI MODELLO: {giocatori_simili}
        - NOTE/ATTREZZATURA: {note_extra}

        DATABASE DRILL VIDEO YOUTUBE:
        {database_video_reali}

        REGOLE FERREE ED INDISPENSIBILI:

        1. CALCOLO TASSATIVO DELLA DURATA ({durata_singola}):
           La somma dei tempi degli esercizi per OGNI GIORNO deve fare ESATTAMENTE {durata_singola}.
           - Se l'utente ha scelto "2 ore" (120 minuti), inserisci un volume adeguato (almeno 6-8 esercizi distinti + riscaldamento + defaticamento).
           - Struttura la sessione così:
             * Riscaldamento e Attivazione: (es. 15 min)
             * Blocco 1 - Tecnica / Signature Drills ({giocatori_simili}): (es. 45 min, 3-4 esercizi)
             * Blocco 2 - Applicazione ad alta intensità / Tiro / Situazionale: (es. 45 min, 3 esercizi)
             * Defaticamento e Stretching: (es. 15 min)
           - PER OGNI ESERCIZIO DEVI INDICARE CHIARAMENTE: [Durata: XX minuti | Serie: X | Ripetizioni: X].

        2. VIDEO DEL SINGOLO ESERCIZIO CON MINUTAGGIO (TIMESTAMP):
           Non inserire un video generale per l'intera scheda. Per OGNI ESERCIZIO della scheda:
           - Prendi il video più pertinente dal DATABASE DRILL VIDEO.
           - Indica il **MINUTAGGIO ESATTO** (timestamp) dove l'utente deve guardare per vedere QUEL SINGOLO ESERCIZIO.
           - Esempio di formattazione da usare sotto l'esercizio:
             **🎥 Video dimostrativo dell'esercizio:**
             [Sintassi immagine dal database]
             👉 [Clicca qui per vedere l'esercizio dal minuto X:XX](URL_BASE&t=SECONDI) (sostituisci SECONDI con il tempo in secondi, es. &t=105s per minuto 1:45).

        3. SINERGIA TRA OBIETTIVO E CAMPIONI:
           Collega sempre le caratteristiche dei giocatori scelti ({giocatori_simili}) all'obiettivo ({obiettivo}) spiegando la meccanica del movimento.

        4. PROGRAMMAZIONE A GIORNI:
           Crea le sezioni "### GIORNO 1", "### GIORNO 2", ecc., in base alla Frequenza ({frequenza}).
        """

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sei un Master Coach NBA rigoroso. Calcoli il minutaggio preciso dell'allenamento ed estrai i timestamp esatti dei video per ogni singolo esercizio."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4500
            )
            
            scheda = chat_completion.choices[0].message.content
            st.success("Programmazione Settimanale Calibrata generata con successo!")
            st.markdown("---")
            st.markdown(scheda, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Errore durante la generazione della scheda: {e}")
