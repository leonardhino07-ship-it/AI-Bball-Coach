import streamlit as st
import json
import os
import datetime
from groq import Groq
from duckduckgo_search import DDGS  # La nuova libreria per la ricerca web!

# ==============================================================================
# CONFIGURAZIONE INIZIALE
# ==============================================================================
st.set_page_config(page_title="AI Basketball Coach (Web Search Edition)", page_icon="🏀", layout="wide")

FILE_PROFILO = "profilo_giocatore.json"
FILE_STORICO = "storico_video.json"

# Inserisci la tua API Key di Groq per provare sul PC
# Usa questa riga per la versione online
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]


def interroga_ai_stream(prompt):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"\n[Errore Groq API: {e}]"


# --- Funzioni di salvataggio/caricamento ---
def carica_json(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def salva_json(file_path, dati):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)


# ==============================================================================
# INTERFACCIA WEB
# ==============================================================================
profilo = carica_json(FILE_PROFILO, {})
storico = carica_json(FILE_STORICO, [])

with st.sidebar:
    st.title("🏀 AI COACH")
    st.caption("Powered by Llama 3 + Web Search 🌐")
    menu = st.radio("Navigazione", ["Profilo Giocatore", "Genera Scheda", "Analisi Video", "Storico Video"])

# --- PAGINA PROFILO ---
if menu == "Profilo Giocatore":
    st.header("👤 Dati del Giocatore")
    with st.form("form_profilo"):
        st.subheader("Informazioni Generali")
        col1, col2 = st.columns(2)
        lingua = col1.text_input("Lingua di output", value=profilo.get("lingua", "Italiano"))
        eta = col2.text_input("Età", value=profilo.get("eta", ""))
        altezza = col1.text_input("Altezza (cm)", value=profilo.get("altezza", ""))
        peso = col2.text_input("Peso (kg)", value=profilo.get("peso", ""))
        ruolo = st.text_input("Ruolo", value=profilo.get("ruolo", ""))

        st.subheader("Stile e Obiettivi")
        esperienza = st.text_input("Anni di esperienza", value=profilo.get("esperienza", ""))
        giocatori_simili = st.text_input("Giocatori di riferimento (Es. Facundo Campazzo)",
                                         value=profilo.get("giocatori_simili", ""))
        obiettivo = st.text_input("Obiettivo", value=profilo.get("obiettivo", ""))

        st.subheader("Logistica")
        compagnia = st.text_input("Con chi ti alleni?", value=profilo.get("compagnia", ""))
        struttura = st.text_input("Struttura (es. campetto, palestra)", value=profilo.get("struttura", ""))

        if st.form_submit_button("💾 Salva Profilo"):
            nuovo_profilo = {
                "lingua": lingua, "eta": eta, "altezza": altezza, "peso": peso,
                "ruolo": ruolo, "esperienza": esperienza, "giocatori_simili": giocatori_simili,
                "obiettivo": obiettivo, "compagnia": compagnia, "struttura": struttura
            }
            salva_json(FILE_PROFILO, nuovo_profilo)
            st.success("Profilo salvato con successo!")
            st.rerun()

# --- PAGINA SCHEDA (CON RICERCA WEB) ---
elif menu == "Genera Scheda":
    st.header("⚡ Crea Scheda Personalizzata")
    if not profilo.get("ruolo"):
        st.warning("Compila il Profilo Giocatore prima di generare una scheda!")
    else:
        col1, col2 = st.columns(2)
        durata = col1.text_input("Durata scheda", value="4 settimane")
        frequenza = col2.text_input("Frequenza", value="3 giorni a settimana")

        if st.button("Genera Scheda NBA", type="primary"):
            giocatori = profilo.get('giocatori_simili', '')
            contesto_web = ""

            # 1. RICERCA WEB IN TEMPO REALE
            if giocatori:
                with st.spinner(f"🌐 Sto cercando su internet gli allenamenti reali di {giocatori}..."):
                    try:
                        # Cerca su DuckDuckGo in inglese per trovare i risultati migliori sul basket
                        query_ricerca = f"{giocatori} basketball workout drills training routine"
                        risultati = DDGS().text(query_ricerca, max_results=3)

                        contesto_web = "\nINFORMAZIONI TROVATE SUL WEB IN TEMPO REALE:\n"
                        for r in risultati:
                            contesto_web += f"- {r['body']}\n"
                    except Exception as e:
                        contesto_web = "(Ricerca web fallita, usa la tua conoscenza base)."

            # 2. GENERAZIONE CON L'IA (Prompt potenziato per massima specificità)
            with st.spinner("🧠 L'IA sta studiando i dati e creando la tua scheda dettagliata..."):
                prompt = f"""Act as an Elite NBA Skills Trainer and Workout Designer. 
                Create a highly detailed, day-by-day training program of {durata} (Freq: {frequenza}).
                Profile: Role {profilo.get('ruolo')}, Experience: {profilo.get('esperienza')}. Target: {profilo.get('obiettivo')}.
                Reference players: {giocatori}.
                Logistics: Trains {profilo.get('compagnia')} in {profilo.get('struttura')}.

                {contesto_web}

                CRITICAL RULES FOR EXERCISES (DO NOT IGNORE): 
                1. NEVER use vague descriptions like "Shooting drills", "Ball handling for 10 mins", or "Pick and roll practice".
                2. For EVERY SINGLE EXERCISE in the workout, you MUST use this exact strict structure:
                   - 🎯 **[Nome Esercizio]**
                   - 📍 **Setup**: Exact court positioning and equipment (e.g., "Put a cone at the top of the key and start at half court").
                   - ⚙️ **Execution**: Step-by-step instructions on what the player must physically do (e.g., "Pound dribble right, cross between legs, explode past cone").
                   - 🔢 **Sets & Reps**: Exact numbers (e.g., "3 sets of 10 MAKES", NEVER "10 minutes").
                   - ⏱️ **Rest**: Specific rest time (e.g., "45 seconds between sets").
                   - 💡 **Pro Tip**: One biomechanical or mental focus point (e.g., "Drop your hips on the crossover").

                3. If I provided "INFORMAZIONI TROVATE SUL WEB", extract the specific drills and format them using the exact structure above.
                4. Translate everything to {profilo.get('lingua', 'Italiano')}, but keep the actual drill names in English if they are common (like "Mikan Drill" or "Pound Crossover")."""

                st.write_stream(interroga_ai_stream(prompt))

# --- PAGINA VIDEO E STORICO RESTANO INVARIATE ---
elif menu == "Analisi Video":
    st.header("🔍 Analisi Sessione Video")
    st.info("Funzione in fase di sviluppo per l'analisi visiva avanzata.")

elif menu == "Storico Video":
    st.header("🕰️ Storico Video")
    if not storico:
        st.info("Nessuna sessione trovata.")