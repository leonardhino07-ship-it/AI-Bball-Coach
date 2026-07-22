import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach PRO", page_icon="🏀", layout="wide")

st.title("🏀 AI Basketball Coach PRO")
st.write("Programmazione settimanale bilanciata con link YouTube DIRETTI e REALI (Nessun video inventato).")

# Controllo della chiave API nei Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
    st.stop()

client = Groq(api_key=groq_api_key)

# MOTORE YOUTUBE: ESTRAE SOLO LINK PURI E REALI
def cerca_video_drills_raw(giocatori, obiettivo):
    db_video_text = ""
    queries = []
    
    lista_g = [g.strip() for g in giocatori.split(',') if g.strip()]
    
    for g in lista_g:
        queries.append(f"{g} signature basketball move drill tutorial")
        queries.append(f"{g} footwork breakdown")

    if obiettivo:
        queries.append(f"basketball {obiettivo} drill tutorial")

    for q in queries[:4]: # Limite a 4 query per non rallentare troppo
        try:
            search = VideosSearch(q, limit=2)
            results = search.result().get('result', [])
            for vid in results:
                v_id = vid.get('id')
                title = vid.get('title', 'Tutorial Esercizio')
                if v_id:
                    clean_url = f"https://www.youtube.com/watch?v={v_id}"
                    
                    db_video_text += f"""
- TITOLO VIDEO: "{title}"
  LINK ESATTO DA COPIARE: {clean_url}
"""
        except Exception:
            pass

    return db_video_text if db_video_text else "NESSUN VIDEO TROVATO. NON INSERIRE ALCUN LINK YOUTUBE."


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
        durata_singola = st.radio("Durata esatta singola sessione:", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 video"])
        logistica = st.radio("Logistica di allenamento:", ["Da solo", "In compagnia"])

    st.subheader("Film Study & Giocatori Modello")
    giocatori_simili = st.text_input("A chi ti ispiri? (Separa con virgola. Es: Stephen Curry, Tyrese Maxey, Kyrie Irving)")
    note_extra = st.text_area("Note (es. infortuni, attrezzi a disposizione come coni, pallina da tennis, spara-palloni)")
    
    submit_button = st.form_submit_button(label="Genera Programmazione Settimanale Sicura")

# ELABORAZIONE
if submit_button:
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
           È SEVERAMENTE VIETATO utilizzare l'ID "dQw4w9WgXcQ" (Rickroll) o qualsiasi altro link non presente nel DATABASE qui sopra.
           Se per un esercizio ritieni utile un video, devi prendere ESATTAMENTE il "LINK ESATTO DA COPIARE" dal database e scriverlo in modo semplice, così:
           👉 **Video di riferimento:** https://www.youtube.com/watch?v=...
           Se non hai un video pertinente nel database per un esercizio, NON inserire alcun link.

        2. REGOLA DI UNIFORMITÀ DEI GIORNI (TASSATIVO):
           In base alla frequenza scelta ({frequenza}), devi creare tutti i giorni previsti (es. "### GIORNO 1", "### GIORNO 2", "### GIORNO 3").
           È SEVERAMENTE VIETATO ridurre la qualità o il numero di esercizi dal Giorno 2 in poi. Ogni singolo giorno deve contenere la stessa quantità di dettagli, serie, ripetizioni e spiegazione biomeccanica dei piedi. 

        3. RISPETTO RIGIDO DEL TEMPO ({durata_singola}):
           Ogni singolo giorno deve essere strutturato per coprire la durata totale di {durata_singola}.
           Tutti gli esercizi di TUTTI i giorni devono avere indicati: [Durata in min | Serie | Ripetizioni | Recupero].
        """

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sei un Master Coach NBA. Inserisci solo link in puro testo (https://...) tratti unicamente dal database fornito. Non inventi mai link YouTube."},
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
            st.error(f"Errore durante la generazione della scheda: {e}")
