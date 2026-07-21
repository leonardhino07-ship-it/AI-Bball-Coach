import streamlit as st
from groq import Groq

# Configurazione della pagina
st.set_page_config(page_title="AI Basketball Coach", page_icon="🏀", layout="centered")

st.title("🏀 AI Basketball Coach")
st.write("Il tuo preparatore atletico e allenatore personale di pallacanestro basato sull'intelligenza artificiale.")

# Controllo della chiave API nei Secrets di Streamlit
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("⚠️ Chiave API di Groq non trovata nei Secrets di Streamlit! Configurala nelle impostazioni della app.")
    st.stop()

# Inizializzazione del client Groq
client = Groq(api_key=groq_api_key)

# Form per la raccolta dei dati
with st.form("coach_form"):
    st.subheader("Profilo del Giocatore e Parametri di Allenamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome del giocatore")
        eta = st.number_input("Età", min_value=5, max_value=60, value=18)
        ruolo = st.selectbox("Ruolo principale", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)", "Tutti i ruoli"])
        livello = st.selectbox("Livello di gioco", ["Principiante", "Intermedio", "Avanzato", "Professionista"])
    
    with col2:
        obiettivo = st.text_input("Obiettivo principale (es. migliorare il tiro da 3, rapidità, palleggio)")
        frequenza = st.selectbox("Frequenza settimanale", ["1-2 volte a settimana", "3-4 volte a settimana", "5+ volte a settimana"])
        
        # NUOVO CAMPO: Durata singolo allenamento
        durata_singola = st.radio(
            "Durata della singola sessione di allenamento:",
            ["30 minuti", "1 ora", "1 ora e 30", "2 ore", "2 ore e 30", "3 ore"]
        )
        
        # NUOVO CAMPO: Logistica
        logistica = st.radio(
            "Come ti alleni solitamente?",
            ["Da solo", "In compagnia"]
        )

    note_extra = st.text_area("Note aggiuntive o particolari esigenze (es. infortuni, preferenze, attrezzi disponibili)")
    
    submit_button = st.form_submit_button(label="Genera Scheda di Allenamento Personalizzata")

# Azione alla pressione del pulsante
if submit_button:
    with st.spinner("L'intelligenza artificiale sta analizzando ogni singolo dato per creare la tua scheda..."):
        
        # Prompt strutturato con obbligo di considerare TUTTI i dati
        prompt = f"""
        Sei un preparatore atletico ed un allenatore di pallacanestro professionista di altissimo livello. 
        Genera una scheda di allenamento di basket dettagliata, professionale e altamente personalizzata basandoti RIGOROSAMENTE E IN MANIERA INTEGRALE su TUTTI i dati forniti dall'utente, dal primo all'ultimo, senza escludere alcun dettaglio:

        DATI INSERITI DALL'UTENTE:
        - Nome: {nome}
        - Età: {eta} anni
        - Ruolo: {ruolo}
        - Livello: {livello}
        - Obiettivo principale: {obiettivo}
        - Frequenza settimanale: {frequenza}
        - Durata della singola sessione: {durata_singola}
        - Modalità di allenamento (Logistica): {logistica}
        - Note/Esigenze extra: {note_extra}

        REGOLE TASSATIVE DA RISPETTARE:
        1. Considera e integra OGNI SINGOLO PARAMETRO sopra elencato nella creazione della scheda. Non trascurare alcuna informazione.
        2. Adatta rigorosamente gli esercizi in base alla modalità di allenamento ({logistica}): se l'utente si allena "Da solo", proponi esercizi individuali (es. ball handling solitario, tiro in autonomia, uso di cinesini); se si allena "In compagnia", includi situazioni di 1v1, passaggio, interazione o difesa attiva.
        3. Il volume, la quantità e l'intensità degli esercizi proposti devono rispecchiare fedelmente ed in modo proporzionato la durata della singola sessione scelta ({durata_singola}).
        4. Struttura la scheda in modo chiaro e pulito: Riscaldamento specifico, Blocco principale focalizzato sull'obiettivo, Esercizi specifici per il ruolo e Cool-down/Stretching finale.
        """

        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Sei un coach di basket esperto, preciso e rigoroso che crea schede dettagliate."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            scheda = chat_completion.choices[0].message.content
            st.success("Scheda generata con successo!")
            st.markdown("---")
            st.markdown(scheda)
            
        except Exception as e:
            st.error(f"Si è verificato un errore durante la generazione della scheda: {e}")
