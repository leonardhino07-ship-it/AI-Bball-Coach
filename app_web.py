import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach", page_icon="🏀", layout="centered")

st.title("🏀 AI Basketball Coach")
st.write("Il tuo preparatore atletico e allenatore personale basato sull'IA, con integrazione YouTube in tempo reale.")

# Controllo della chiave API nei Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
    st.stop()

client = Groq(api_key=groq_api_key)

# FUNZIONE MOTORE DI RICERCA YOUTUBE
def cerca_migliori_video_youtube(giocatori):
    risultati_totali = ""
    lista_giocatori = [g.strip() for g in giocatori.split(',')]
    
    for giocatore in lista_giocatori:
        if not giocatore: continue
        try:
            # Cerca fino a 15 video per avere un ampio margine di scelta
            search = VideosSearch(f"{giocatore} basketball workout drills training", limit=15)
            videos = search.result()['result']
            
            # Funzione per estrarre e convertire in numero le visualizzazioni (es. da "1.2M views" a 1200000)
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

            # Ordina i video partendo da quello con PIÙ visualizzazioni
            videos_ordinati = sorted(videos, key=get_views, reverse=True)
            
            # Preleva i 2 video in assoluto più visti (i più autorevoli)
            risultati_totali += f"\n--- VIDEO REALI PIÙ VISTI SU YOUTUBE PER: {giocatore.upper()} ---\n"
            for vid in videos_ordinati[:2]:
                titolo = vid.get('title', 'Titolo Sconosciuto')
                link = vid.get('link', '#')
                views = vid.get('viewCount', {}).get('text', 'Visualizzazioni sconosciute')
                risultati_totali += f"- Titolo: {titolo} | Visualizzazioni: {views} | Link Reale: {link}\n"
        except Exception as e:
            risultati_totali += f"Impossibile recuperare video per {giocatore}.\n"
            
    return risultati_totali


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
        obiettivo = st.text_input("Obiettivo principale (es. migliorare tiro, rapidità)")
        frequenza = st.selectbox("Frequenza settimanale", ["1-2 volte", "3-4 volte", "5+ volte"])
        durata_singola = st.radio("Durata della singola sessione:", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
        logistica = st.radio("Come ti alleni solitamente?", ["Da solo", "In compagnia"])

    # NUOVO CAMPO: Giocatori Simili
    st.subheader("Analisi Stile di Gioco (Film Study)")
    giocatori_simili = st.text_input("Quali giocatori hanno uno stile simile al tuo o a chi ti ispiri? (Separa i nomi con una virgola. Es: Milos Teodosic, Payton Pritchard)")

    note_extra = st.text_area("Note aggiuntive (es. infortuni, attrezzi disponibili)")
    
    submit_button = st.form_submit_button(label="Genera Scheda e Cerca Video YouTube")

# ELABORAZIONE
if submit_button:
    # 1. Fase di Ricerca Web
    video_trovati = "Nessun giocatore specifico inserito per la ricerca YouTube."
    if giocatori_simili.strip():
        with st.spinner("Sto scansionando YouTube per trovare i video di allenamento più visualizzati dei giocatori scelti..."):
            video_trovati = cerca_migliori_video_youtube(giocatori_simili)
            st.success("Ricerca YouTube completata!")

    # 2. Fase di Generazione IA
    with st.spinner("L'IA sta costruendo la tua scheda personalizzata analizzando i dati e i video..."):
        prompt = f"""
        Sei un preparatore atletico ed un allenatore di pallacanestro professionista. 
        Genera una scheda di allenamento dettagliata, professionale e personalizzata basandoti RIGOROSAMENTE su TUTTI i seguenti dati, nessuno escluso:

        DATI UTENTE:
        - Nome: {nome}
        - Età: {eta} anni | Ruolo: {ruolo} | Livello: {livello}
        - Obiettivo principale: {obiettivo}
        - Frequenza: {frequenza} | Durata singola sessione: {durata_singola}
        - Modalità: {logistica}
        - Note extra: {note_extra}

        RICERCA YOUTUBE AUTOMATICA (FILM STUDY):
        L'utente si ispira a questi giocatori: {giocatori_simili}. 
        Il nostro sistema ha trovato in automatico i seguenti video di allenamento su YouTube (ordinati per essere i più visti e autorevoli):
        {video_trovati}

        REGOLE TASSATIVE DA RISPETTARE:
        1. Considera e integra OGNI SINGOLO PARAMETRO utente.
        2. Adatta gli esercizi alla modalità ({logistica}): esercizi individuali se è "Da solo", situazioni 1v1 o di passaggio se "In compagnia".
        3. Il volume degli esercizi deve essere realistico per la durata scelta ({durata_singola}).
        4. DEVI ASSOLUTAMENTE integrare i video reali di YouTube trovati nel testo. Inserisci i Titoli e i Link forniti spiegando brevemente l'esercizio o il movimento che il giocatore deve studiare dal video. Non inventare link YouTube finti.
        """

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sei un coach di basket esperto, preciso e rigoroso. Integri fonti web reali nei tuoi allenamenti."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            scheda = chat_completion.choices[0].message.content
            st.markdown("---")
            st.markdown(scheda)
            
        except Exception as e:
            st.error(f"Errore durante la generazione della scheda: {e}")
