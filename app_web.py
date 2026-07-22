import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach PRO", page_icon="🏀", layout="wide")

st.title("🏀 AI Basketball Coach PRO")
st.write("Programmazione settimanale bilanciata con link YouTube HTML garantiti e pari dettaglio per ogni giorno.")

# Controllo della chiave API nei Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
    st.stop()

client = Groq(api_key=groq_api_key)

# MOTORE YOUTUBE CON GENERAZIONE DI LINK HTML ESTERNI (target="_blank")
def cerca_video_drills_html(giocatori, obiettivo):
    db_video_text = ""
    queries = []
    
    lista_g = [g.strip() for g in giocatori.split(',') if g.strip()]
    
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
                title = vid.get('title', 'Tutorial Esercizio').replace('[', '').replace(']', '').replace('"', "'")
                if v_id:
                    # Garantiamo il prefisso https:// completo e l'apertura in nuova scheda
                    clean_url = f"https://www.youtube.com/watch?v={v_id}"
                    thumb_url = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"
                    
                    # Codice HTML bloccato per evitare errori di reindirizzamento
                    html_block = f'<a href="{clean_url}" target="_blank" style="text-decoration:none;"><img src="{thumb_url}" width="260" style="border-radius:8px;"><br>👉 <b>Guarda su YouTube: {title}</b></a>'
                    
                    db_video_text += f"""
- DRILL VIDEO: "{title}"
  URL_BASE: {clean_url}
  CODICE_HTML_DA_INCOLLARE: {html_block}
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
    
    submit_button = st.form_submit_button(label="Genera Programmazione Settimanale")

# ELABORAZIONE
if submit_button:
    with st.spinner("Scansione database YouTube per trovare i singoli drill dei campioni..."):
        database_video_reali = cerca_video_drills_html(giocatori_simili, obiettivo)

    with st.spinner("L'IA sta costruendo la scheda garantendo pari dettaglio per OGNI giorno..."):
        prompt = f"""
        Sei un MENTORE E PREPARATORE ATLETICO NBA di livello mondiale.
        Il tuo compito è creare un PROGRAMMA DI ALLENAMENTO SETTIMANALE iper-dettagliato, senza alcuna vaghezza e mantenendo la STESSA identica cura dal primo all'ultimo giorno.

        DATI UTENTE TASSATIVI:
        - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
        - OBIETTIVO PRINCIPALE: {obiettivo}
        - FREQUENZA SETTIMANALE: {frequenza}
        - DURATA SINGOLA SESSIONE: {durata_singola}
        - LOGISTICA: {logistica} (SE "DA SOLO": VIETATI PASSAGGI E DIFENSORI REALI)
        - GIOCATORI MODELLO: {giocatori_simili}
        - NOTE/ATTREZZATURA: {note_extra}

        DATABASE VIDEO HTML REALI DA INCOLLARE:
        {database_video_reali}

        REGOLE FERREE ED INDISPENSIBILI:

        1. REGOLA DI UNIFORMITÀ DEI GIORNI (TASSATIVO):
           In base alla frequenza scelta ({frequenza}), devi creare tutti i giorni previsti (es. "### GIORNO 1", "### GIORNO 2", "### GIORNO 3", "### GIORNO 4").
           È SEVERAMENTE VIETATO ridurre la qualità o il numero di esercizi dal Giorno 2 in poi. Ogni singolo giorno deve contenere la stessa quantità di dettagli, serie, ripetizioni, spiegazione biomeccanica dei piedi e video tutorial. Non scrivere mai frasi come "ripeti il giorno 1" o "fai esercizi simili".

        2. RISPETTO RIGIDO DEL TEMPO ({durata_singola}):
           Ogni singolo giorno deve essere strutturato per coprire la durata totale di {durata_singola}:
           - Riscaldamento/Attivazione
           - Blocco Tecnica & Signature Drills ({giocatori_simili})
           - Blocco Applicazione & Tiro/Situazionale
           - Defaticamento
           Tutti gli esercizi di TUTTI i giorni devono avere indicati: [Durata in min | Serie | Ripetizioni | Recupero].

        3. LINK E VIDEO GARANTITI (HTML):
           Sotto ogni esercizio principale, per mostrare il video, DEVI incollare l'esatto codice fornito sotto la voce "CODICE_HTML_DA_INCOLLARE" del database. Se vuoi specificare un minutaggio (timestamp), aggiungi sotto una riga in questo modo:
           👉 <a href="URL_BASE&t=SECONDI" target="_blank"><b>Guarda l'esercizio dal minuto X:XX su YouTube</b></a>
           Nessun link deve rimanere privo del prefisso https:// e dell'attributo target="_blank".
        """

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sei un Master Coach NBA. Mantieni un livello di dettaglio maniacale e identico per tutti i giorni della scheda. Usi solo tag HTML con target='_blank' per i link."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2, # Temperatura ancora più bassa per forzare il rispetto maniacale della struttura e non 'stancarsi' nei giorni successivi
                max_tokens=4500
            )
            
            scheda = chat_completion.choices[0].message.content
            st.success("Programmazione Settimanale Uniforme e Completa generata!")
            st.markdown("---")
            st.markdown(scheda, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Errore durante la generazione della scheda: {e}")
