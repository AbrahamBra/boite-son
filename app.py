import streamlit as st
import google.generativeai as genai
import os
import tempfile
import time
import pathlib
import re
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="🎹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS PREMIUM (INTÉGRAL) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #E0E0E0;
    }
    
    .stApp { background-color: #0E1117; }
    [data-testid="stSidebar"] { background-color: #0E1117; border-right: 1px solid #1F1F1F; }

    h1 { font-weight: 600; letter-spacing: -1px; color: #FFFFFF; }
    h2, h3 { font-weight: 400; color: #A0A0A0; }

    /* Inputs & Buttons */
    .stTextInput > div > div > input {
        background-color: #161920; border: 1px solid #303030; color: white; border-radius: 8px;
    }
    .stButton > button {
        background-color: #161920; color: white; border: 1px solid #303030; border-radius: 8px; font-weight: 500;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child button {
        background-color: #FFFFFF; color: #000000; border: none;
    }
    
    /* Upload Zones */
    div[data-testid="stFileUploader"] {
        background-color: #12141A; border: 1px dashed #303030; border-radius: 12px; padding: 20px;
    }
    /* Cache les labels uploader moches */
    div[data-testid="stFileUploader"] label { display: none; }
    div[data-testid="stFileUploader"] { margin-top: -10px; }
    
    /* Chat Messages */
    .stChatMessage { background-color: rgba(255, 255, 255, 0.02); border: 1px solid #333; border-radius: 12px; margin-bottom: 10px; }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 3rem; padding-bottom: 5rem;}
    
    /* Info Box */
    div[data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.05); border: 1px solid #303030; color: #E0E0E0; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DICTIONNAIRE COMPLET (FRANÇAIS & ANGLAIS RESTAURÉS) ---
TR = {
    "Français 🇫🇷": {
        "settings": "1. Configuration",
        "api_label": "Clé API Google",
        "api_help": "ℹ️ Pourquoi une clé perso ?",
        "api_desc": "Projet open-source. L'usage de votre propre clé gratuite garantit votre indépendance et la gratuité totale de l'outil.",
        "doc_section": "2. Votre Machine",
        "doc_help": "🔍 Trouver mon manuel officiel",
        "manual_upload": "Déposer le Manuel PDF ici",
        "manual_loaded": "Manuel OK",
        "audio_title": "🎧 Le Son à Analyser",
        "audio_subtitle": "C'est ici que la magie opère. Glissez un fichier pour lancer l'écoute.",
        "audio_label": "Fichier Audio",
        "coach_section": "🧪 Mode Coach (Comparaison)",
        "coach_desc": "Charge ton propre essai ici. L'IA comparera ton son avec la cible.",
        "coach_label": "Mon Essai (mp3/wav)",
        "vision_section": "👁️ Vision Debug",
        "vision_desc": "Montre tes réglages (Photo)",
        "vision_toggle": "Activer Caméra / Upload",
        "style_section": "3. Style Pédagogique",
        "memory_title": "4. 💾 Session & Mémoire",
        "memory_help": "💡 Comment ça marche ?",
        "memory_desc": "**Sauvegarder votre progression :**\n\n1. En fin de session, cliquez sur **💾 Télécharger** en bas\n2. Un fichier .txt sera téléchargé avec tout l'historique\n3. La prochaine fois, glissez ce fichier ici pour reprendre\n\nL'IA se souviendra de tout le contexte !",
        "memory_load": "📂 Reprendre une session précédente",
        "memory_save": "💾 Télécharger Session",
        "reset": "🔄 Nouvelle Session",
        "about": "📖 Philosophie du projet",
        "about_text": """**Groovebox Tutor** est né d'une frustration : celle de voir des musiciens acheter des machines incroyables... pour finalement copier des presets trouvés sur Reddit.

### Notre vision

Nous croyons que **comprendre** vaut mieux que **copier**. Que la vraie créativité vient de la maîtrise technique. Que chaque machine mérite qu'on apprenne à lui parler.

### Comment ça marche

L'IA agit comme votre **binôme de studio** :
- 🎧 Elle écoute votre référence sonore
- 📖 Elle lit le manuel de votre machine
- 🎛️ Elle vous guide pour **recréer** le son par vous-même

Pas de preset tout fait. Pas de solution miracle. Juste de la **pédagogie**, étape par étape.""",
        "support": "☕ Soutenir (Don)",
        "title": "Groovebox Tutor",
        "subtitle": "Votre binôme technique. Décryptez le son. Maîtrisez votre machine.",
        "placeholder": "Posez une question technique sur ce son...",
        "onboarding": "👋 **Objectif : Autonomie**\n\n1. Importez le **Manuel** de votre instrument (à gauche)\n2. Proposez un **Son** qui vous inspire (ci-dessous)\n3. Votre binôme analyse la texture et vous enseigne **les étapes techniques** pour recréer ce grain vous-même",
        "legal": "⚠️ Outil d'analyse à but éducatif. L'inspiration est légale, le plagiat ne l'est pas.",
        "sugg_1": "Analyse ce son",
        "sugg_2": "Structure rythmique",
        "sugg_3": "Fonction cachée",
        "style_label": "Approche Pédagogique",
        "tones": ["🤙 Mentor Cool", "👔 Expert Technique", "⚡ Synthétique"],
        "formats": ["📝 Cours Complet", "✅ Checklist", "💬 Interactif"],
        "manual_loaded": "✅ Manuel assimilé",
        "active_track": "Piste active :",
        "session_reloaded": "✅ Session rechargée ! L'IA se souvient du contexte.",
        "analyzing": "🧠 Analyse pédagogique en cours..."
    },
    "English 🇬🇧": {
        "settings": "1. Setup",
        "api_label": "Google API Key",
        "api_help": "ℹ️ Why a personal key?",
        "api_desc": "Open-source project. Using your own free key ensures your independence and total tool freedom.",
        "doc_section": "2. Your Gear",
        "doc_help": "🔍 Find official manual",
        "manual_upload": "Drop PDF Manual here",
        "manual_loaded": "Manual OK",
        "audio_title": "🎧 The Sound",
        "audio_subtitle": "Magic happens here. Drop your audio file.",
        "audio_label": "Audio File",
        "coach_section": "🧪 Coach Mode (Comparison)",
        "coach_desc": "Upload your attempt here. AI will compare it with the target.",
        "coach_label": "My Attempt (mp3/wav)",
        "vision_section": "👁️ Vision Debug",
        "vision_desc": "Show your settings (Photo)",
        "vision_toggle": "Enable Camera / Upload",
        "style_section": "3. Teaching Style",
        "memory_title": "4. 💾 Session & Memory",
        "memory_help": "💡 How does it work?",
        "memory_desc": "**Save your progress:**\n\n1. At the end of your session, click **💾 Download** below\n2. A .txt file will be downloaded with all the history\n3. Next time, drop that file here to resume\n\nThe AI will remember all context!",
        "memory_load": "📂 Resume previous session",
        "memory_save": "💾 Download Session",
        "reset": "🔄 New Session",
        "about": "📖 Project Philosophy",
        "about_text": """**Groovebox Tutor** was born from frustration: watching musicians buy incredible machines... only to copy presets from Reddit.

### Our vision

We believe **understanding** beats **copying**. That real creativity comes from technical mastery. That every machine deserves to be learned properly.

### How it works

The AI acts as your **studio partner**:
- 🎧 It listens to your reference sound
- 📖 It reads your machine's manual
- 🎛️ It guides you to **recreate** the sound yourself""",
        "support": "☕ Donate",
        "title": "Groovebox Tutor",
        "subtitle": "Your technical partner. Decode sound. Master your gear.",
        "placeholder": "Ask a technical question about this sound...",
        "onboarding": "👋 **Goal: Autonomy**\n\n1. Upload your instrument's **Manual** (left sidebar)\n2. Provide a **Sound** that inspires you (below)\n3. Your partner analyzes the texture and teaches you **the technical steps** to recreate it yourself",
        "legal": "⚠️ Educational analysis tool. Inspiration is legal, plagiarism is not.",
        "sugg_1": "Analyze sound",
        "sugg_2": "Rhythm structure",
        "sugg_3": "Hidden feature",
        "style_label": "Teaching Approach",
        "tones": ["🤙 Cool Mentor", "👔 Technical Expert", "⚡ Direct"],
        "formats": ["📝 Full Lesson", "✅ Checklist", "💬 Interactive"],
        "manual_loaded": "✅ Manual loaded",
        "active_track": "Active track:",
        "session_reloaded": "✅ Session reloaded! The AI remembers the context.",
        "analyzing": "🧠 Analysis in progress..."
    }
}

# --- 4. FONCTIONS SYSTÈME ---
def format_history_for_context(history):
    """
    Transforme l'historique visuel du chat en texte brut pour le 'cerveau' de l'IA.
    C'est ça qui permet à l'IA de se souvenir que tu as choisi 'Basse'.
    """
    context_str = "\n--- DÉBUT DE L'HISTORIQUE DE CONVERSATION (CONTEXTE) ---\n"
    # On prend les 10 derniers échanges pour avoir un bon contexte
    for msg in history[-10:]:
        role = "UTILISATEUR" if msg['role'] == "user" else "GROOVEBOX TUTOR (TOI)"
        context_str += f"{role}: {msg['content']}\n"
    context_str += "--- FIN DE L'HISTORIQUE ---\n"
    return context_str

def build_system_prompt(user_level, has_manual, chat_context_str):
    
    # 1. LOGIQUE DE NIVEAU STRICTE
    if "Débutant" in user_level:
        level_instr = """
        🚨 MODE : DÉBUTANT ABSOLU (PAS À PAS).
        Ton interlocuteur ne connait PAS le jargon.
        RÈGLE 1 : Ne donne JAMAIS plus d'une instruction physique à la fois.
        RÈGLE 2 : Guide le doigt de l'utilisateur ("Appuie sur le bouton AMP en haut à droite").
        RÈGLE 3 : Si l'utilisateur confirme ("C'est fait", "Ok", "Basse"), PASSE À L'ÉTAPE SUIVANTE immédiatement sans blabla.
        """
    elif "Expert" in user_level:
        level_instr = "MODE : EXPERT. Sois concis. Donne les tables de valeurs (0-127), les CC MIDI et les pages du manuel."
    else:
        level_instr = "MODE : INTERMÉDIAIRE. Explique le concept sonore (enveloppe, filtre) puis dis quel menu ouvrir."

    manual_instr = "Tu as le manuel chargé. Cite la PAGE exacte pour chaque affirmation." if has_manual else "Base-toi sur tes connaissances générales de cette machine."

    # 2. PROMPT SYSTÈME FINAL
    return f"""
    Tu es "Groovebox Tutor", un coach expert en hardware musical.
    
    TA MISSION : Aider l'utilisateur à refaire le son qu'il t'a envoyé (Fichier Audio) sur sa machine (Manuel).
    
    INSTRUCTIONS PÉDAGOGIQUES :
    {level_instr}
    
    INSTRUCTIONS MANUEL :
    {manual_instr}
    
    IMPORTANT - GESTION DE LA CONVERSATION :
    Lis attentivement l'HISTORIQUE ci-dessous.
    Si l'utilisateur répond à une de tes questions (exemple: tu as demandé "Quel instrument ?", il répond "Kick"),
    NE DIS PAS "Ah super choix le kick".
    DONNE DIRECTEMENT LA PREMIÈRE ÉTAPE TECHNIQUE pour faire le kick sur sa machine.
    
    {chat_context_str}
    """
    elif "Expert" in user_level:
        level_instr = "MODE : EXPERT. Sois concis. Donne les tables de valeurs, les numéros de CC MIDI et les pages du manuel. Pas de blabla."
    else:
        level_instr = "MODE : INTERMÉDIAIRE. Explique le concept de synthèse (ex: 'On va sculpter l'enveloppe') puis guide vers les bons menus."

    manual_instr = "Tu as le manuel. Cite la PAGE exacte pour chaque affirmation." if has_manual else "Base-toi sur tes connaissances générales de cette machine."

    # PROMPT SYSTÈME
    return f"""
    Tu es "Groovebox Tutor", un coach expert en hardware musical.
    
    TA CIBLE MACHINE : L'utilisateur possède une machine spécifique (voir manuel ou contexte).
    TON RÔLE : Guider l'utilisateur pour recréer le son qu'il entend (Fichier Cible) sur sa propre machine.
    
    {level_instr}
    
    {manual_instr}
    
    RÈGLE D'OR DE LA CONVERSATION :
    Regarde l'HISTORIQUE ci-dessous.
    Si l'utilisateur répond à une question que tu as posée (ex: tu as demandé "Kick ou Basse ?", il répond "Basse"),
    NE DIS PAS "Génial j'adore la basse".
    COMMENCE IMMÉDIATEMENT LE TUTORIEL POUR LA BASSE.
    
    {chat_context_str}
    """

# --- 5. LOGIQUE PRINCIPALE ---

# A. SETUP
if "chat_history" not in st.session_state: st.session_state.chat_history = []
T = TR["Français 🇫🇷"]

# B. SIDEBAR
with st.sidebar:
    st.header("1. Configuration")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key: 
        try:
            genai.configure(api_key=api_key)
        except: st.error("Clé invalide")

    st.markdown("---")
    st.header("🎓 Pédagogie")
    user_level = st.radio("Ton Niveau", ["Débutant (Pas à pas)", "Intermédiaire (Guide)", "Expert (Valeurs)"])
    style_tone = st.selectbox("Ton", ["Mentor Cool", "Strict", "Direct"])
    
    st.markdown("---")
    st.header("2. Fichiers")
    
    # PDF
    uploaded_pdf = st.file_uploader("Manuel (PDF)", type=["pdf"])
    if uploaded_pdf and "pdf_ref" not in st.session_state and api_key:
        with st.status("Lecture du manuel...", expanded=False):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
                t.write(uploaded_pdf.getvalue()); path=t.name
            ref = genai.upload_file(path, mime_type="application/pdf")
            while ref.state.name == "PROCESSING": time.sleep(1); ref = genai.get_file(ref.name)
            st.session_state.pdf_ref = ref
            st.session_state.auto_trigger = "AUTO_MANUAL"
            st.rerun()
    if "pdf_ref" in st.session_state: st.success("✅ Manuel chargé")

    # AUDIO
    uploaded_audio = st.file_uploader("Son à copier (Audio)", type=["mp3", "wav", "m4a"])
    if uploaded_audio and api_key:
        if "audio_name" not in st.session_state or st.session_state.audio_name != uploaded_audio.name:
            with st.status("Analyse audio...", expanded=False):
                suffix = f".{uploaded_audio.name.split('.')[-1]}"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as t:
                    t.write(uploaded_audio.getvalue()); path=t.name
                ref = genai.upload_file(path)
                while ref.state.name == "PROCESSING": time.sleep(0.5); ref = genai.get_file(ref.name)
                st.session_state.audio_ref = ref
                st.session_state.audio_name = uploaded_audio.name
                st.session_state.auto_trigger = "AUTO_ANALYSE"
                st.rerun()
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

# C. MAIN UI
st.title(T["title"])
st.caption(T["subtitle"])

if not api_key:
    st.warning("⚠️ Clé API requise.")
else:
    # AFFICHER CHAT
    chat_container = st.container()
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    # GESTION TRIGGERS AUTOMATIQUES
    prompt = None
    trigger = st.session_state.get("auto_trigger")

    if trigger == "AUTO_MANUAL":
        prompt = "👋 [SYSTÈME] J'ai chargé le manuel. Dis-moi que tu es prêt et demande quel est mon objectif."
        st.session_state.auto_trigger = None 

    elif trigger == "AUTO_ANALYSE":
        prompt = "🔥 [SYSTÈME] Analyse ce fichier audio. Identifie les éléments (Kick, Snare, Basse, etc.) et demande-moi par lequel je veux commencer."
        st.session_state.auto_trigger = None 
    
    else:
        # INPUT UTILISATEUR STANDARD
        user_input = st.chat_input(T["placeholder"])
        if user_input:
            prompt = user_input
            # Affichage immédiat user
            with chat_container:
                with st.chat_message("user"): st.markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

    # GENERATION IA
    if prompt:
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(T["analyzing"]):
                    try:
                        # 1. Récupérer l'historique sous forme de texte
                        chat_context = format_history_for_context(st.session_state.chat_history)
                        
                        # 2. Construire le prompt système avec ce contexte
                        sys_prompt = build_system_prompt(
                            "Français", style_tone, user_level, 
                            "pdf_ref" in st.session_state,
                            chat_context # <--- C'EST ICI QUE LA MAGIE OPÈRE
                        )

                        # 3. Préparer la requête (Fichiers + Prompt actuel)
                        req = []
                        if "pdf_ref" in st.session_state: req.append(st.session_state.pdf_ref)
                        if "audio_ref" in st.session_state: req.extend(["Voici le fichier audio cible :", st.session_state.audio_ref])
                        
                        req.append(prompt)

                        # 4. Appel Modèle
                        # Note : J'utilise gemini-1.5-flash ou pro car le 2.0-exp est instable pour le contexte parfois
                        model = genai.GenerativeModel("gemini-2.0-flash-exp", system_instruction=sys_prompt)
                        resp = model.generate_content(req)
                        
                        # 5. Affichage et Sauvegarde
                        st.markdown(resp.text)
                        st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
                        
                    except Exception as e:
                        st.error(f"Erreur IA : {e}")


