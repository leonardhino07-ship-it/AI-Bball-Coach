import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach PRO", page_icon="🏀", layout="wide")

st.title("🏀 AI Basketball Coach PRO")
st.write("Generatore di schede settimanali con Video Tutorial Reali integrati.")

# Controllo della chiave API nei Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
    st.stop()

client = Groq(api_key=groq_api_key)

# FUNZIONE DI RICERCA YOUTUBE POTENZIATA (Estrae Link e Copertine/Thumbnails)
def genera_database_video(giocatori, obiettivo):
    db_video = ""
    
    # 1. Ricerca mirata sull'obiettivo dell'utente
    if obiettivo:
        try:
            search_obj = VideosSearch(f"basketball {obiettivo} drills tutorial", limit=5)
            for vid in search_obj.result()['result']:
                titolo = vid.get('title', 'Tutorial').replace('[', '').replace(']', '')
                link = vid.get('link', '')
                # Prende l'URL della copertina del video pulendo i parametri extra
                thumb = vid.get('thumbnails', [{}])[0].get('url', '').split('?')[0] 
                if link and thumb:
                    db_video += f"\n- TITOLO: {titolo}\n  CODICE DA INCOLLARE: [![{titolo}]({thumb})]({link})\n"
        except Exception as e:
            pass
            
    # 2. Ricerca mirata sui giocatori scelti
    if giocatori:
        lista_g = [g.strip() for g in giocatori.split(',') if g.strip()]
        for g in lista_g:
            try:
                search_g = VideosSearch(f"{g} basketball workout drills", limit=3)
                for vid in search_g.result()['result']:
                    titolo = vid.get('title', f'Video su {g}').replace('[', '').replace(']', '')
                    link = vid.get('link', '')
                    thumb = vid.get('thumbnails', [{}])[0].get('url', '').split('?')[0]
                    if link and thumb:
                        db_video += f"\n- TITOLO: {titolo}\n  CODICE DA INCOLLARE: [![{titolo}]({thumb})]({link})\n"
            except Exception as e:
                pass
                
    return db_video if db_video else "Nessun video specifico trovato."


# INTERFACCIA UTENTE
with st.form("coach_form"):
    st.subheader("Parametri di Allenamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome del giocatore")
        eta = st.number_input("Età", min_value=5, max_value=60, value=18)
        ruolo = st.selectbox("Ruolo principale", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
        livello = st.selectbox("Livello di gioco", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
    
    with col2:
        obiettivo = st.text_input("Obiettivo preciso (es. tiro dal palleggio, footwork, difesa)")
        frequenza = st.selectbox("Frequenza settimanale", ["1-2 volte", "3-4 volte", "5+ volte"])
        durata_singola = st.radio("Durata esatta singola sessione:", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
        logistica = st.radio("Logistica di allenamento:", ["Da solo", "In compagnia"])

    st.subheader("Film Study (Studio dei Giocatori)")
    giocatori_simili = st.text_input("Giocatori di riferimento (es: Kyrie Irving, Luka Doncic)")
    note_extra = st.text_area("Note (es. infortuni, attrezzi a disposizione)")
    
    submit_button = st.form_submit_button(label="Genera Scheda Settimanale Completa")

# ELABORAZIONE
if submit_button:
    with st.spinner("Scansione di YouTube per estrarre le copertine dei video reali..."):
        database_video_reali = genera_database_video(giocatori_simili, obiettivo)

    with st.spinner("Creazione della programmazione settimanale in corso..."):
        prompt = f"""
        Sei un preparatore atletico NBA. Crea un PROGRAMMA DI ALLENAMENTO SETTIMANALE iper-dettagliato.
        
        DATI UTENTE TASSATIVI:
        - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
        - Obiettivo Focus: {obiettivo}
        - Frequenza Settimanale: {frequenza}
        - Durata Singola Sessione: {durata_singola}
        - Logistica: {logistica} (SE È "DA SOLO" NON INSERIRE PASSAGGI O DIFENSORI)
        - Modelli: {giocatori_simili}
        - Note: {note_extra}

        DATABASE VIDEO YOUTUBE REALI:
        Qui sotto hai una lista di video reali appena trovati su YouTube. Sotto ad alcuni esercizi, DEVI copiare e incollare l'esatto "CODICE DA INCOLLARE" del video più pertinente. Questo mostrerà la copertina cliccabile all'utente.
        {database_video_reali}

        REGOLE FERREE:
        1. STRUTTURA SETTIMANALE: Basandoti sulla "Frequenza Settimanale" ({frequenza}), dividi la scheda in giorni. Esempio: se è "3-4 volte", crea l'intestazione "### GIORNO 1", "### GIORNO 2", "### GIORNO 3".
        2. DIVERSIFICAZIONE: Ogni giorno deve concentrarsi su una sfumatura diversa dell'obiettivo.
        3. DURATA: Il volume di OGNI GIORNO deve coincidere con la "Durata Singola Sessione" ({durata_singola}).
        4. DETTAGLIO ESERCIZI: Nessuna vaghezza. Indica Nome esercizio, Serie, Ripetizioni e Meccanica esatta (come muovere i piedi, dove guardare).
        5. INSERIMENTO VIDEO: Dopo la spiegazione di un esercizio chiave, scrivi "**🎥 Guarda il video di riferimento:**" e poi incolla il codice del video preso dal DATABASE VIDEO fornito sopra. NON INVENTARE LINK.
        """

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sei un coach rigoroso. Strutturi piani settimanali e usi SOLO i codici video forniti nel database."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, # Molto bassa per massima precisione e nessuna invenzione di link
                max_tokens=4500
            )
            
            scheda = chat_completion.choices[0].message.content
            st.success("Programmazione Settimanale generata con successo!")
            st.markdown("---")
            st.markdown(scheda, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Errore durante la generazione della scheda: {e}")
