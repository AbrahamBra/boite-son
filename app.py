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

# --- 4. FONCTIONS SYSTÈME & MÉMOIRE (OPTIMISÉES) ---

def format_history_for_context(history):
    """
    Transforme TOUT l'historique en texte.
    Gemini 1.5 a une mémoire immense, on ne limite plus aux 10 derniers messages.
    """
    context_str = "\n--- 💾 MÉMOIRE DE LA SESSION (HISTORIQUE COMPLET) ---\n"
    for msg in history:
        role = "L'ÉLÈVE (UTILISATEUR)" if msg['role'] == "user" else "LE COACH (TOI)"
        context_str += f"{role}: {msg['content']}\n"
    context_str += "--- FIN MÉMOIRE ---\n"
    return context_str

def build_system_prompt(lang, style_tone, user_level, has_manual, chat_context, trigger_mode=None):
    
    # 1. DÉFINITION DES PERSONAS (STYLE)
    personas = {
        "Mentor Cool": "Tu es un pote musicien. Tu tutoies. Tu es encourageant. Tu utilises des emojis. Ton but est que l'utilisateur s'amuse.",
        "Expert Technique": "Tu es un ingénieur son strict. Tu vouvoies. Tu es précis, froid et chirurgical. Pas de blabla, que des faits.",
        "Synthétique": "Tu es un robot d'assistance. Réponses ultra-courtes (max 2 phrases). Style télégraphique."
    }
    selected_persona = personas.get(style_tone, personas["Mentor Cool"])

    # 2. CALIBRAGE DU NIVEAU (PÉDAGOGIE STRICTE)
    if "Débutant" in user_level:
        level_instr = """
        🚨 MODE : DÉBUTANT ABSOLU (NOOB TOTAL)
        L'utilisateur est perdu. Il ne connaît PAS le vocabulaire (LFO, Filtre, Enveloppe = Interdit).
        
        TES RÈGLES D'OR :
        1. Une seule action physique à la fois. (Ex: "Tourne le bouton A").
        2. Attends que l'utilisateur dise "Ok" ou "Fait" avant de donner la suite.
        3. Ne donne JAMAIS d'explication théorique ("On fait ça pour éclaircir le son"). On s'en fiche. On veut juste que ça marche.
        4. Guide-le géographiquement ("Le bouton rouge en haut à gauche").
        """
    elif "Expert" in user_level:
        level_instr = """
        🧠 MODE : EXPERT
        L'utilisateur connaît sa machine. Ne l'insulte pas avec des instructions basiques.
        Donne les valeurs MIDI (0-127), les fréquences en Hz, et les pages du manuel.
        Sois dense et technique.
        """
    else:
        level_instr = """
        🎓 MODE : INTERMÉDIAIRE
        L'utilisateur veut comprendre.
        Explique d'abord le concept ("On va réduire l'attaque pour avoir un son percussif").
        Puis donne la manipulation ("Menu AMP > Attack > 0").
        """

    manual_instr = "Tu as le manuel PDF en mémoire : cite toujours la page correspondante." if has_manual else "Base-toi sur tes connaissances de la machine."
    
    # 3. ASSEMBLAGE DU PROMPT
    base = f"""
    Tu es Groovebox Tutor.
    
    TON PERSONA : {selected_persona}
    
    TES INSTRUCTIONS PÉDAGOGIQUES :
    {level_instr}
    
    SOURCE DOCUMENTAIRE :
    {manual_instr}
    
    CONTEXTE ACTUEL :
    {chat_context}
    
    ⚡ INTERDICTION FORMELLE :
    Si l'historique montre que tu as posé une question (ex: "Kick ou Snare ?") et que l'utilisateur a répondu ("Kick"),
    NE FAIS PAS DE COMMENTAIRES INUTILES ("Ah super choix !").
    DÉMARRE IMMÉDIATEMENT L'INSTRUCTION N°1 pour le Kick.
    """
    
    # 4. GESTION DES TRIGGERS (ACTION RÉFLEXE)
    if trigger_mode == "AUTO_ANALYSE":
        return base + """
        🚨 PRIORITÉ ABSOLUE : NOUVEAU FICHIER AUDIO DÉTECTÉ.
        Ne dis pas bonjour.
        1. Analyse le style et les instruments du fichier audio.
        2. Fais une liste à puces des éléments détectés (Kick, Bass, Lead...).
        3. Demande à l'utilisateur : "Par quoi veux-tu commencer ?"
        """
    elif trigger_mode == "AUTO_COACH":
        return base + """
        🚨 PRIORITÉ ABSOLUE : COMPARAISON D'ESSAI.
        L'utilisateur tente de copier le son.
        1. Donne une note de ressemblance /100.
        2. Identifie LE paramètre principal qui cloche (ex: "Ton son est trop sourd").
        3. Dis quel bouton tourner pour corriger.
        """
    elif trigger_mode == "AUTO_MANUAL":
        return base + """
        🚨 PRIORITÉ ABSOLUE : MANUEL REÇU.
        Confirme juste la marque et le modèle de la machine détectée dans le PDF.
        Demande : "Veux-tu un tuto sound design ou une explication de fonction ?"
        """
    elif trigger_mode == "VISION":
        return base + """
        🚨 PRIORITÉ ABSOLUE : ANALYSE VISUELLE.
        Regarde la photo des réglages.
        Compare avec ce qu'il faudrait pour le son cible.
        Si un bouton est mal placé, dis-le (ex: "Ton Cutoff est trop bas, ouvre-le vers 14h").
        """
    
    return base

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


