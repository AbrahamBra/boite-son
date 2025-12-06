import streamlit as st
import google.generativeai as genai
import os
import tempfile
import time
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="🎹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS PREMIUM (DESIGN COMPLET) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
    }
    .stApp { background-color: #0E1117; }
    [data-testid="stSidebar"] { background-color: #0E1117; border-right: 1px solid #1F1F1F; }
    h1 { font-weight: 600; letter-spacing: -1px; color: #FFFFFF; }
    h2, h3 { font-weight: 400; color: #A0A0A0; }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: #161920; border: 1px solid #303030; color: white; border-radius: 8px;
    }
    .stButton > button {
        background-color: #161920; color: white; border: 1px solid #303030; border-radius: 8px; font-weight: 500;
    }
    
    /* Uploaders Stylisés */
    div[data-testid="stFileUploader"] {
        background-color: #12141A; border: 1px dashed #303030; border-radius: 12px; padding: 20px;
    }
    div[data-testid="stFileUploader"] label { display: none; }
    div[data-testid="stFileUploader"] { margin-top: -10px; }
    
    /* Messages Chat */
    .stChatMessage { background-color: rgba(255, 255, 255, 0.02); border: 1px solid #333; border-radius: 12px; margin-bottom: 10px; }
    
    /* Info Box */
    div[data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.05); border: 1px solid #303030; color: #E0E0E0; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DICTIONNAIRE RICHE (TEXTES RESTAURÉS) ---
TR = {
    "Français 🇫🇷": {
        "settings": "1. Configuration",
        "api_label": "Clé API Google",
        "api_help": "ℹ️ Pourquoi une clé perso ?",
        "api_desc": "Projet open-source. L'usage de votre propre clé gratuite garantit votre indépendance.",
        "doc_section": "2. Votre Machine",
        "doc_help": "🔍 Trouver mon manuel officiel",
        "manual_upload": "Déposer le Manuel PDF ici",
        "manual_loaded": "Manuel OK",
        "audio_title": "🎧 Le Son à Analyser",
        "audio_label": "Fichier Audio",
        "coach_section": "🧪 Mode Coach (Comparaison)",
        "coach_desc": "Charge ton propre essai ici.",
        "coach_label": "Mon Essai (mp3/wav)",
        "vision_section": "👁️ Vision Debug",
        "vision_desc": "Montre tes réglages (Photo)",
        "vision_toggle": "Activer Caméra / Upload",
        "style_section": "3. Style Pédagogique",
        "about": "📖 Philosophie du projet",
        "about_text": """**Groovebox Tutor** est né d'une frustration : celle de voir des musiciens acheter des machines incroyables... pour finalement copier des presets.

### Notre vision
Nous croyons que **comprendre** vaut mieux que **copier**.
L'IA n'est pas un chatbot passif. C'est un **Coach Proactif**.

*Fait avec ❤️ pour les beatmakers.*""",
        "title": "Groovebox Tutor",
        "subtitle": "Votre binôme technique. Décryptez le son. Maîtrisez votre machine.",
        "placeholder": "Pose une question technique...",
        "analyzing": "🧠 Analyse pédagogique en cours..."
    }
}

# --- 4. FONCTIONS SYSTÈME & MÉMOIRE (CORRIGÉES) ---

def format_history_for_context(history):
    """
    Transforme TOUT l'historique en texte.
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
        RÈGLES D'OR :
        1. Une seule action physique à la fois. (Ex: "Tourne le bouton A").
        2. Attends que l'utilisateur dise "Ok" avant de passer à la suite.
        3. Guide-le géographiquement ("Le bouton rouge en haut à gauche").
        """
    elif "Expert" in user_level:
        level_instr = "MODE : EXPERT. Donne les valeurs MIDI (0-127), fréquences Hz, et pages du manuel. Sois dense."
    else:
        level_instr = "MODE : INTERMÉDIAIRE. Explique le concept puis donne la manipulation."

    manual_instr = "Cite toujours la page du manuel PDF." if has_manual else "Base-toi sur tes connaissances."
    
    # 3. ASSEMBLAGE DU PROMPT (CORRIGÉ : PLUS DE DOUBLON ICI)
    base = f"""
    Tu es Groovebox Tutor (Powered by Gemini 2.0).
    
    TON PERSONA : {selected_persona}
    TES INSTRUCTIONS PÉDAGOGIQUES : {level_instr}
    SOURCE DOCUMENTAIRE : {manual_instr}
    
    CONTEXTE ACTUEL :
    {chat_context}
    
    ⚡ INTERDICTION FORMELLE :
    Si l'historique montre que tu as posé une question (ex: "Kick ou Snare ?") et que l'utilisateur a répondu ("Kick"),
    NE FAIS PAS DE COMMENTAIRES INUTILES. DÉMARRE IMMÉDIATEMENT L'INSTRUCTION N°1.
    """
    
    # 4. GESTION DES TRIGGERS (ACTION RÉFLEXE)
    if trigger_mode == "AUTO_ANALYSE":
        return base + """
        🚨 PRIORITÉ ABSOLUE : NOUVEAU FICHIER AUDIO DÉTECTÉ.
        1. Analyse le style et les instruments.
        2. Fais une liste à puces des éléments détectés.
        3. Demande à l'utilisateur : "Par quoi veux-tu commencer ?"
        """
    elif trigger_mode == "AUTO_COACH":
        return base + """
        🚨 PRIORITÉ ABSOLUE : COMPARAISON D'ESSAI.
        1. Donne une note de ressemblance /100.
        2. Identifie LE paramètre principal qui cloche.
        3. Dis quel bouton tourner pour corriger.
        """
    elif trigger_mode == "AUTO_MANUAL":
        return base + """
        🚨 PRIORITÉ ABSOLUE : MANUEL REÇU.
        Confirme le modèle de la machine. Demande : "Veux-tu un tuto sound design ou une explication de fonction ?"
        """
    elif trigger_mode == "VISION":
        return base + """
        🚨 PRIORITÉ ABSOLUE : ANALYSE VISUELLE.
        Regarde la photo des réglages. Compare avec ce qu'il faudrait pour le son cible.
        """
    
    return base

# --- 5. LOGIQUE PRINCIPALE ---

# A. SETUP
if "chat_history" not in st.session_state: st.session_state.chat_history = []
T = TR["Français 🇫🇷"]

# B. SIDEBAR
with st.sidebar:
    st.header(T['settings'])
    api_key = st.text_input(T['api_label'], type="password", key="api_key_sidebar")
    with st.expander(T['api_help']):
        st.caption(T['api_desc'])

    if api_key: 
        try:
            genai.configure(api_key=api_key)
        except: st.error("Clé invalide")

    st.markdown("---")
    st.header("🎓 Pédagogie")
    user_level = st.radio("Ton Niveau", ["Débutant (Pas à pas)", "Intermédiaire (Guide)", "Expert (Valeurs)"], key="user_level_radio")
    style_tone = st.selectbox("Ton", ["Mentor Cool", "Expert Technique", "Synthétique"], key="style_tone_select")
    
    st.markdown("---")
    st.header(T['doc_section'])
    
    # PDF
    uploaded_pdf = st.file_uploader(T['manual_upload'], type=["pdf"], key="pdf_uploader")
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

    st.markdown("---")
    # AUDIO
    st.header(T['audio_title'])
    uploaded_audio = st.file_uploader(T['audio_label'], type=["mp3", "wav", "m4a"], key="audio_uploader")
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
    
    st.markdown("---")
    # ESSAI
    with st.expander(T['coach_section']):
        st.caption(T['coach_desc'])
        uploaded_try = st.file_uploader(T['coach_label'], type=["mp3", "wav", "m4a"], key="try_uploader")
        if uploaded_try and api_key:
            if "try_name" not in st.session_state or st.session_state.get("try_name") != uploaded_try.name:
                 with st.status("Comparaison...", expanded=False):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                        t.write(uploaded_try.getvalue()); path=t.name
                    ref = genai.upload_file(path)
                    while ref.state.name == "PROCESSING": time.sleep(0.5); ref = genai.get_file(ref.name)
                    st.session_state.try_ref = ref
                    st.session_state.try_name = uploaded_try.name
                    st.session_state.auto_trigger = "AUTO_COACH"
                    st.rerun()
    
    st.markdown("---")
    # VISION
    st.markdown(f"### {T['vision_section']}")
    img_mode = st.toggle(T['vision_toggle'], key="vision_toggle_btn")
    uploaded_img = None
    if img_mode:
        tab1, tab2 = st.tabs(["📸", "📂"])
        with tab1: 
            cam = st.camera_input("Photo", key="camera_input")
            if cam: uploaded_img = cam
        with tab2: 
            up = st.file_uploader("Image", type=["jpg", "png"], key="image_uploader")
            if up: uploaded_img = up
    
    if uploaded_img:
        st.session_state.vision_ref = Image.open(uploaded_img)
        st.toast("Vision active")

    st.markdown("---")
    with st.expander(T["about"]):
        st.markdown(T["about_text"])

    if st.button("🗑️ Reset Chat", key="reset_button"):
        st.session_state.chat_history = []
        st.rerun()

# C. MAIN UI (AFFICHAGE DU CHAT EN PREMIER)
st.title(T["title"])
st.caption(T["subtitle"])

if not api_key:
    st.warning("⚠️ Clé API requise.")
else:
    # 1. D'ABORD : AFFICHER L'HISTORIQUE (Pour qu'il ne disparaisse jamais)
    chat_container = st.container()
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    # 2. LOGIQUE DE TRAITEMENT (EN ARRIÈRE-PLAN)
    # Placée ici pour que le Chat reste affiché pendant le chargement
    
    # A. Traitement PDF
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.sidebar.status("Lecture du manuel...", expanded=False):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
                t.write(uploaded_pdf.getvalue()); path=t.name
            ref = genai.upload_file(path, mime_type="application/pdf")
            while ref.state.name == "PROCESSING": time.sleep(1); ref = genai.get_file(ref.name)
            
            st.session_state.pdf_ref = ref
            st.session_state.auto_trigger = "AUTO_MANUAL"
            # Petit message visuel immédiat dans le chat
            st.session_state.chat_history.append({"role": "user", "content": "📂 [SYSTEM] J'ai chargé le manuel."})
            st.rerun()

    # B. Traitement Audio (CORRIGÉ)
    # On utilise une logique simplifiée pour éviter le bug d'affichage
    if uploaded_audio:
        # On vérifie si c'est un nouveau fichier en comparant le nom
        is_new_audio = "audio_name" not in st.session_state or st.session_state.audio_name != uploaded_audio.name
        
        if is_new_audio:
            with st.sidebar.status("Analyse audio en cours...", expanded=False):
                suffix = f".{uploaded_audio.name.split('.')[-1]}"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as t:
                    t.write(uploaded_audio.getvalue()); path=t.name
                
                # Upload Gemini
                ref = genai.upload_file(path)
                # Attente active (important pour l'audio)
                while ref.state.name == "PROCESSING": time.sleep(1); ref = genai.get_file(ref.name)
                
                # Mise à jour Session
                st.session_state.audio_ref = ref
                st.session_state.audio_name = uploaded_audio.name
                st.session_state.auto_trigger = "AUTO_ANALYSE"
                
                # Feedback Chat
                st.session_state.chat_history.append({"role": "user", "content": f"🎧 [SYSTEM] Analyse de : {uploaded_audio.name}"})
                st.rerun()

    # C. Traitement Essai
    if uploaded_try:
        is_new_try = "try_name" not in st.session_state or st.session_state.get("try_name") != uploaded_try.name
        
        if is_new_try:
             with st.sidebar.status("Comparaison spectrale...", expanded=False):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                    t.write(uploaded_try.getvalue()); path=t.name
                
                ref = genai.upload_file(path)
                while ref.state.name == "PROCESSING": time.sleep(1); ref = genai.get_file(ref.name)
                
                st.session_state.try_ref = ref
                st.session_state.try_name = uploaded_try.name
                st.session_state.auto_trigger = "AUTO_COACH"
                st.session_state.chat_history.append({"role": "user", "content": "🧪 [SYSTEM] J'ai envoyé mon essai pour correction."})
                st.rerun()