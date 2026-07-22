import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach PRO", page_icon="🏀", layout="wide")

st.title("🏀 AI Basketball Coach PRO")
st.write("Programmazione settimanale basata sui Signature Drills dei campioni e video tutorial verificati.")

# Controllo della chiave API nei Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
    st.stop()

client = Groq(api_key=groq_api_key)

# MOTORE DI RICERCA YOUTUBE A LINK GARANTITI (Usa gli ID fissi di Google/YouTube)
def cerca_video_garantiti(giocatori, obiettivo):
    db_video_text = ""
    queries = []
    
    # Mappatura termini in inglese per trovare i migliori tutorial su YouTube
    dizionario_termini = {
        "primo passo": "first step explosiveness drill",
        "palleggio": "ball handling handles drill",
        "handles": "ball handling tennis ball drill",
        "tiro": "shooting form drill",
        "tiro da tre": "3pt shooting drill",
        "difesa": "defense footwork drill",
        "finiture": "finishing layups drill",
        "floater": "floater drill",
        "arresto e tiro": "pull up jumper drill"
    }
    
    obj_en = obiettivo.lower()
    for k, v in dizionario_termini.items():
        if k in obj_en:
            obj_en = v
            break

    lista_g = [g.strip() for g in giocatori.split(',') if g.strip()]
    
    # 1. Cerca esercizi specifici incrociando Giocatore + Obiettivo
    for g in lista_g:
        queries.append(f"{g} {obj_en} workout drill")
        queries.append(f"{g} signature basketball move tutorial")

    # 2. Cerca tutorial generali sull'obiettivo
    if obiettivo:
        queries.append(f"basketball {obj_en} tutorial")

    for q in queries[:4]: # Limite a 4 ricerche per massima velocità
        try:
            search = VideosSearch(q, limit=2)
            results = search.result().get('result', [])
            for vid in results:
                v_id = vid.get('id')
                title = vid.get('title', 'Video Tutorial').replace('[', '').replace(']', '').replace('"', '')
                if v_id:
                    # Costruzione link puliti e permanenti
                    clean_url = f"https://www.youtube.com/watch?v={v_id}"
                    thumb_url = f"https://img.youtube.com/vi/{v_id}/hqdefault.jpg"
                    
                    db_video_text += f"""
- VIDEO: "{title}"
  LNK: {clean_url}
  IMG: {thumb_url}
  SINTASSI DA INCOLLARE:
  [![{title}]({thumb_url})]({clean_url})
  👉 [Guarda il video su YouTube: {title}]({clean_url})
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
    giocatori_simili = st.text_input("A chi ti ispiri? (Separa con virgola. Es: Stephen Curry, Tyrese Maxey, Kyrie Irving, Jalen Brunson)")
    note_extra = st.text_area("Note (es. infortuni, attrezzi a disposizione come coni, pallina da tennis, spara-palloni)")
    
    submit_button = st.form_submit_button(label="Genera Scheda Settimanale Sinergica")

# ELABORAZIONE
if submit_button:
    with st.spinner("Scansione database YouTube e verifica dei link permanenti..."):
        database_video_reali = cerca_video_garantiti(giocatori_simili, obiettivo)

    with st.spinner("L'IA sta analizzando la sinergia tra i tuoi obiettivi e le abilità dei campioni..."):
        prompt = f"""
        Sei un MENTORE E PREPARATORE ATLETICO NBA di livello mondiale.
        Il tuo compito è creare un PROGRAMMA DI ALLENAMENTO SETTIMANALE basato sulla SINERGIA tra l'obiettivo dell'utente e i suoi giocatori modello.

        DATI UTENTE:
        - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
        - OBIETTIVO PRINCIPALE: {obiettivo}
        - FREQUENZA SETTIMANALE: {frequenza}
        - DURATA SINGOLA SESSIONE: {durata_singola}
        - LOGISTICA: {logistica} (SE "DA SOLO": VIETATI PASSAGGI E DIFENSORI REALI)
        - GIOCATORI MODELLO: {giocatori_simili}
        - NOTE/ATTREZZATURA: {note_extra}

        DATABASE VIDEO REALI VERIFICATI DA INSERIRE:
        {database_video_reali}

        REGOLE FONDAMENTALI DI SINERGIA E STRUTTURA:
        1. ANALISI SINERGICA (OBBLIGATORIA IN APERTURA):
           All'inizio della scheda, crea la sezione "🧠 ANALISI DELLE CARATTERISTICHE E SIGNATURE DRILLS".
           Spiega ESATTAMENTE come le abilità dei giocatori inseriti ({giocatori_simili}) si collegano all'obiettivo ({obiettivo}).
           - Esempio: Se l'obiettivo è il palleggio/handles e tra i giocatori c'è Stephen Curry, inserisci l'iconico esercizio Curry con pallina da tennis + pallone da basket.
           - Esempio: Se l'obiettivo è il primo passo e c'è Tyrese Maxey o Russell Westbrook, inserisci gli esercizi di accelerazione/decelerazione e primo passo esplosivo che usano loro.
           - Esempio: Se c'è Kyrie Irving, inserisci esercizi di "heavy ball" o finiture acrobatiche sul tabellone.

        2. PROGRAMMAZIONE A GIORNI:
           Dividi la scheda in base alla Frequenza ({frequenza}) creando le sezioni "### GIORNO 1", "### GIORNO 2", ecc.
           Ogni giorno deve avere un focus specifico e la durata totale degli esercizi di ogni giorno deve corrispondere esattamente a "{durata_singola}".

        3. INTEGRITÀ DEI LINK VIDEO (FONDAMENTALE):
           Dopo aver spiegato un esercizio chiave o un Signature Drill, DEVI inserire il video di riferimento prendendo il blocco dal DATABASE VIDEO sopra.
           Copia e incolla ESATTAMENTE il blocco "SINTASSI DA INCOLLARE" fornito per quel video. NON MODIFICARE L'URL. NON INVENTARE LINK.

        4. DETTAGLIO CLINICO:
           Indica sempre Nome Esercizio, Serie, Ripetizioni, Tempi di Recupero e la spiegazione biomeccanica dei piedi e del corpo.
        """

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sei un Master Coach NBA. Conosci tutte le routine di allenamento dei giocatori NBA ed europei. Incolli SOLO i link video forniti nel database senza modificarli."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, # Bassa per evitare allucinazioni e garantire precisione
                max_tokens=4500
            )
            
            scheda = chat_completion.choices[0].message.content
            st.success("Programmazione Settimanale Sinergica generata con successo!")
            st.markdown("---")
            st.markdown(scheda, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Errore durante la generazione della scheda: {e}")
