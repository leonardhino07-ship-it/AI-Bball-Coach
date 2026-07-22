import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch
import urllib.parse

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach", page_icon="🏀", layout="centered")

st.title("🏀 AI Basketball Coach")
st.write("Il tuo allenatore personale basato sull'IA con video dimostrativi per ogni esercizio (YouTube & TikTok).")

# Controllo della chiave API nei Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
    st.stop()

client = Groq(api_key=groq_api_key)

# FUNZIONE MOTORE DI RICERCA YOUTUBE (Con ordinamento per visualizzazioni)
def cerca_migliori_video_youtube(query_ricerca, limite=10):
    try:
        search = VideosSearch(query_ricerca, limit=limite)
        videos = search.result()['result']
        
        def get_views(vid):
            testo_views = vid.get('viewCount', {}).get('text', '0')
            if not testo_views: return 0
            s = testo_views.lower().replace(',', '').replace(' views', '').replace(' visualizzazioni', '').strip()
            moltiplicatore = 1
            if 'k' in s:
                moltiplicatore = 1000
                s = s.replace('k', '')
            elif 'm' in s:
                moltiplicatore = 1000000
                s = s.replace('m', '')
            try:
                return int(float(s) * moltiplicatore)
            except:
                return 0

        videos_ordinati = sorted(videos, key=get_views, reverse=True)
        
        risultati = []
        for vid in videos_ordinati[:3]: # Preleva i 3 video più visti
            titolo = vid.get('title', 'Titolo Sconosciuto')
            link = vid.get('link', '#')
            views = vid.get('viewCount', {}).get('text', 'Visualizzazioni sconosciute')
            risultati.append(f"- [{titolo}]({link}) (Visualizzazioni: {views})")
            
        return "\n".join(risultati)
    except Exception as e:
        return "Impossibile recuperare video al momento."

# FUNZIONE GENERATRICE LINK TIKTOK
def genera_link_tiktok(query):
    query_encoded = urllib.parse.quote(f"basketball {query} drill tutorial")
    return f"https://www.tiktok.com/search?q={query_encoded}"


# INTERFACCIA UTENTE
with st.form("coach_form"):
    st.subheader("Profilo del Giocatore e Parametri di Allenamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome del giocatore")
        eta = st.number_input("Età", min_value=5, max_value=60, value=18)
        ruolo = st.selectbox("Ruolo principale", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
        livello = st.selectbox("Livello di gioco", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
    
    with col2:
        obiettivo = st.text_input("Obiettivo principale (es. tiro da tre, palleggio esitazione, primo passo)")
        frequenza = st.selectbox("Frequenza settimanale", ["1-2 volte", "3-4 volte", "5+ volte"])
        durata_singola = st.radio("Durata della singola sessione:", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
        logistica = st.radio("Come ti alleni solitamente?", ["Da solo", "In compagnia"])

    # Giocatori Simili (Film Study)
    st.subheader("Analisi Stile di Gioco (Film Study)")
    giocatori_simili = st.text_input("A quali giocatori ti ispiri o quali hanno uno stile simile al tuo? (Separa con una virgola. Es: Milos Teodosic, Payton Pritchard)")

    note_extra = st.text_area("Note aggiuntive (es. infortuni, attrezzi disponibili)")
    
    submit_button = st.form_submit_button(label="Genera Scheda con Video Tutorial (YouTube & TikTok)")

# ELABORAZIONE
if submit_button:
    # 1. Fase di Ricerca Video
    with st.spinner("Sto scansionando i migliori tutorial su YouTube e preparando i link per TikTok..."):
        
        # Ricerca video per Giocatori Simili
        video_giocatori = ""
        if giocatori_simili.strip():
            video_giocatori = cerca_migliori_video_youtube(f"{giocatori_simili} basketball workout drills")
        
        # Ricerca video specifici per l'Obiettivo scelto
        query_obiettivo = obiettivo if obiettivo else "basketball fundamentals"
        video_esercizi = cerca_migliori_video_youtube(f"how to {query_obiettivo} basketball drill tutorial")
        
        # Link TikTok per l'obiettivo
        link_tiktok_generale = genera_link_tiktok(query_obiettivo)

    # 2. Fase di Generazione IA
    with st.spinner("L'IA sta creando la scheda inserendo i link ai video per ogni esercizio..."):
        prompt = f"""
        Sei un preparatore atletico ed un allenatore di pallacanestro professionista. 
        Genera una scheda di allenamento dettagliata, professionale e personalizzata basandoti RIGOROSAMENTE su TUTTI i seguenti dati:

        DATI UTENTE:
        - Nome: {nome}
        - Età: {eta} anni | Ruolo: {ruolo} | Livello: {livello}
        - Obiettivo principale: {obiettivo}
        - Frequenza: {frequenza} | Durata singola sessione: {durata_singola}
        - Modalità: {logistica}
        - Giocatori di riferimento: {giocatori_simili}
        - Note extra: {note_extra}

        FONTI E VIDEO TROVATI DAL SISTEMA:
        - Video YouTube più visti per i giocatori di riferimento:
        {video_giocatori}

        - Video YouTube più visti per l'obiettivo ({obiettivo}):
        {video_esercizi}

        - Link di ricerca TikTok dedicato:
        [Guarda i Reel e Tutorial su TikTok]({link_tiktok_generale})

        REGOLE FONDAMENTALI DI STRUTTURAZIONE SCHEDA:
        1. Rispetta tutti i parametri dell'utente (durata {durata_singola}, modalità {logistica}, livello {livello}).
        2. Per OGNI esercizio o movimento tecnico inserito nella scheda:
           - Spiega chiaramente l'esecuzione tecnica.
           - Aggiungi sempre una riga: **"🎥 GUARDA IL VIDEO/TUTORIAL:"** inserendo sia il link YouTube reale fornito sopra, sia invitando l'utente a cliccare sul link TikTok [Guarda su TikTok]({link_tiktok_generale}) per vedere brevi Reel dimostrativi della mossa.
        3. Assicurati che tutti i link YouTube siano quelli reali forniti nel prompt.
        """

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sei un coach di basket esperto. Integri sempre link video cliccabili (YouTube e TikTok) per permettere all'utente di studiare l'esecuzione visiva di ogni esercizio."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3500
            )
            
            scheda = chat_completion.choices[0].message.content
            st.markdown("---")
            st.markdown(scheda)
            
        except Exception as e:
            st.error(f"Errore durante la generazione della scheda: {e}")
