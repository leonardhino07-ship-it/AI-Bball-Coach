import streamlit as st
from groq import Groq
from youtubesearchpython import VideosSearch

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach", page_icon="🏀", layout="centered")

st.title("🏀 AI Basketball Coach PRO")
st.write("Schede di allenamento iper-dettagliate con analisi dei movimenti e integrazione video.")

# Controllo della chiave API nei Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit!")
    st.stop()

client = Groq(api_key=groq_api_key)

# FUNZIONE MOTORE DI RICERCA YOUTUBE OTTIMIZZATA
def cerca_migliori_video_youtube(giocatori):
    risultati_totali = ""
    lista_giocatori = [g.strip() for g in giocatori.split(',') if g.strip()]
    
    if not lista_giocatori:
        return "Nessun giocatore inserito."

    for giocatore in lista_giocatori:
        try:
            # Ricerca semplificata per garantire sempre risultati (sia per star che per role player)
            query = f"{giocatore} basketball workout highlights skills"
            search = VideosSearch(query, limit=10)
            videos = search.result()['result']
            
            # Filtro base per prendere i 2 video più rilevanti
            risultati_totali += f"\n--- VIDEO STUDIO PER: {giocatore.upper()} ---\n"
            for vid in videos[:2]:
                titolo = vid.get('title', 'Titolo Sconosciuto')
                link = vid.get('link', '#')
                risultati_totali += f"- [{titolo}]({link})\n"
        except Exception as e:
            risultati_totali += f"- Impossibile estrarre link diretti per {giocatore}. L'IA suggerirà le parole chiave esatte per la ricerca.\n"
            
    return risultati_totali


# INTERFACCIA UTENTE
with st.form("coach_form"):
    st.subheader("Profilo del Giocatore e Parametri (Compila con cura)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome del giocatore")
        eta = st.number_input("Età", min_value=5, max_value=60, value=18)
        ruolo = st.selectbox("Ruolo principale", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
        livello = st.selectbox("Livello di gioco", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
    
    with col2:
        obiettivo = st.text_input("Obiettivo preciso (es. palleggio arresto e tiro, floater, difesa sull'uomo)")
        frequenza = st.selectbox("Frequenza settimanale", ["1-2 volte", "3-4 volte", "5+ volte"])
        durata_singola = st.radio("Durata esatta sessione:", ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"])
        logistica = st.radio("Logistica di allenamento:", ["Da solo", "In compagnia"])

    st.subheader("Film Study (Studio dei Giocatori)")
    giocatori_simili = st.text_input("Giocatori di riferimento (Separa con virgola. Es: Jalen Brunson, Austin Reaves, Facundo Campazzo)")
    note_extra = st.text_area("Note (es. infortuni, attrezzi a disposizione come coni, palla medica, spara-palloni)")
    
    submit_button = st.form_submit_button(label="Genera Scheda Professionale Avanzata")

# ELABORAZIONE
if submit_button:
    with st.spinner("Ricerca dei video di riferimento in corso..."):
        video_trovati = cerca_migliori_video_youtube(giocatori_simili)

    with st.spinner("L'IA sta assemblando gli esercizi al dettaglio. Nessuna indicazione vaga consentita..."):
        prompt = f"""
        Sei un preparatore atletico NBA ed un allenatore di pallacanestro di altissimo livello.
        Il tuo compito è creare una scheda di allenamento ESTREMAMENTE PRECISA, TECNICA e DETTAGLIATA.
        VIETATO ESSERE VAGHI. Non scrivere mai frasi generiche come "fai un po' di palleggio" o "esercitati al tiro".
        Devi fornire esercizi specifici, meccaniche di movimento, serie, ripetizioni e tempi di recupero.

        DATI TASSATIVI DELL'UTENTE (Devi basare TUTTA la scheda su questi, senza ignorarne nessuno):
        - Nome: {nome} | Età: {eta} | Ruolo: {ruolo} | Livello: {livello}
        - Obiettivo Focus: {obiettivo}
        - Durata Sessione: {durata_singola}
        - Modalità (Logistica): {logistica}
        - Giocatori Modello: {giocatori_simili}
        - Note fisiche/attrezzatura: {note_extra}

        VIDEO RECUPERATI DAL SISTEMA:
        {video_trovati}

        REGOLE FERREE PER LA CREAZIONE DELLA SCHEDA:
        1. ADATTAMENTO LOGISTICO: Se l'utente ha scelto "Da solo", è SEVERAMENTE VIETATO inserire esercizi che richiedono passaggi da un compagno o difensori reali. Inventa auto-passaggi o uso di ostacoli/sedie. Se ha scelto "In compagnia", sfrutta i compagni per passaggi, letture e 1v1.
        2. GESTIONE DEL TEMPO: La somma dei minuti di tutti gli esercizi deve coincidere esattamente con "{durata_singola}".
        3. FILM STUDY PRATICO: Analizza i "Signature Moves" (mosse tipiche) dei giocatori modello ({giocatori_simili}) e inserisci esercizi SPECIFICI per replicare le loro meccaniche esatte.
        4. FORMATO DI OGNI ESERCIZIO: Ogni singolo esercizio DEVE avere questa struttura:
           - **Nome Esercizio** (es. Mikan Drill Inverso, Esitazione Drop e Tiro)
           - **Durata/Serie/Ripetizioni**: (es. 3 Serie da 10 tiri segnati, recupero 45 sec)
           - **Meccanica ed Esecuzione Dettagliata**: Spiega ESATTAMENTE come muovere i piedi, dove guardare, come posizionare il corpo.
           - Se applicabile, inserisci il link YouTube fornito sopra o consiglia la ricerca esatta da fare su Google/YouTube (es. "Cerca: 'Jalen Brunson footwork drill'").

        La scheda deve iniziare con un paragrafo intitolato "ANALISI DEL PROFILO" in cui confermi all'utente come hai strutturato il workout tenendo conto della durata, della logistica e del livello inseriti.
        """

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sei un allenatore di basket professionista, cinico e precisissimo. Rifiuti la vaghezza e fornisci solo dettagli tecnici di alto livello."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4, # Abbassata la temperatura per risposte più logiche, precise e meno creative/vaghe
                max_tokens=4000
            )
            
            scheda = chat_completion.choices[0].message.content
            st.success("Scheda professionale generata con successo!")
            st.markdown("---")
            st.markdown(scheda)
            
        except Exception as e:
            st.error(f"Errore durante la generazione della scheda: {e}")
