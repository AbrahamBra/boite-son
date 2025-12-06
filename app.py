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
    page_title="Groovebox Tutor Pro",
    page_icon="🎹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS PREMIUM (INTÉGRAL & PRESERVÉ) ---
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
    
    /* Chat Messages */
    .stChatMessage { background-color: rgba(255, 255, 255, 0.02); border: 1px solid #222; border-radius: 10px; }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 3rem; padding-bottom: 5rem;}
    
    /* Info Box */
    div[data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.05); border: 1px solid #303030; color: #E0E0E0; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DICTIONNAIRE COMPLET (TEXTES RICHES) ---
TR = {
    "Français 🇫🇷": {
        "settings": "1. Configuration",
        "api_label": "Clé API Google",
        "api_help": "ℹ️ Pourquoi une clé perso ?",
        "api_desc": "Projet open-source. L'usage de votre propre clé gratuite garantit votre indépendance.",
        "doc_section": "2. Votre Machine",
        "doc_help": "🔍 Trouver mon manuel officiel",
        "manual_upload": "Déposer le Manuel PDF ici",
        "level_label": "Ton niveau actuel",
        "levels": ["Débutant (Explique-moi)", "Intermédiaire (Guide-moi)", "Expert (Valeurs brutes)"],
        "audio_title": "🎧 Le Son à Analyser",
        "audio_subtitle": "Glissez un fichier ici. L'IA l'analysera AUTOMATIQUEMENT.",
        "audio_label": "Fichier Audio",
        "coach_section": "🧪 Mode Coach (Comparaison)",
        "coach_desc": "Charge ton propre essai ici. L'IA te donnera une NOTE sur 100.",
        "coach_label": "Mon Essai (mp3/wav)",
        "vision_section": "👁️ Vision Debug",
        "vision_desc": "Montre tes réglages (Photo)",
        "vision_toggle": "Activer Caméra / Upload",
        "style_section": "3. Style Pédagogique",
        "memory_title": "4. 💾 Session & Mémoire",
        "memory_desc": "**Sauvegarder votre progression :**\nCliquez sur **💾 Télécharger** pour récupérer l'historique.",
        "memory_load": "📂 Reprendre une session précédente",
        "memory_save": "💾 Télécharger Session",
        "reset": "🔄 Nouvelle Session",
        "about": "📖 Philosophie du projet",
        "about_text": """**Groovebox Tutor** est né d'une frustration : celle de voir des musiciens acheter des machines incroyables... pour finalement copier des presets trouvés sur Reddit.

### Notre vision
Nous croyons que **comprendre** vaut mieux que **copier**.
L'IA n'est pas un chatbot passif. C'est un **Coach Proactif** qui :
- 👂 Écoute dès que vous chargez un son.
- 📊 Vous donne la recette technique précise.
- 🏆 Vous note sur vos essais.

*Fait avec ❤️ pour les beatmakers.*""",
        "support": "☕ Soutenir (Don)",
        "title": "Groovebox Tutor",
        "subtitle": "Votre binôme technique. Décryptez le son. Maîtrisez votre machine.",
        "placeholder": "Posez une question ou laissez l'IA analyser...",
        "sugg_1": "Analyse ce son",
        "sugg_2": "Structure rythmique",
        "sugg_3": "Fonction cachée",
        "style_label": "Approche Pédagogique",
        "tones": ["🤙 Mentor Cool", "👔 Expert Technique", "⚡ Synthétique"],
        "formats": ["📝 Cours Complet", "✅ Checklist", "💬 Interactif"],
        "manual_loaded": "✅ Manuel assimilé",
        "active_track": "Piste active :",
        "session_reloaded": "✅ Session rechargée !"
    },
    "English 🇬🇧": {
        "settings": "1. Setup",
        "api_label": "Google API Key",
        "api_help": "ℹ️ Why a personal key?",
        "api_desc": "Open-source project. Using your own free key ensures your independence.",
        "doc_section": "2. Your Gear",
        "doc_help": "🔍 Find official manual",
        "manual_upload": "Drop PDF Manual here",
        "audio_title": "🎧 The Sound",
        "audio_subtitle": "Drop a file here. AI will analyze it AUTOMATICALLY.",
        "audio_label": "Audio File",
        "coach_section": "🧪 Coach Mode (Comparison)",
        "coach_desc": "Upload your attempt here. AI will give you a SCORE out of 100.",
        "coach_label": "My Attempt (mp3/wav)",
        "vision_section": "👁️ Vision Debug",
        "vision_desc": "Show your settings (Photo)",
        "vision_toggle": "Enable Camera / Upload",
        "style_section": "3. Teaching Style",
        "memory_title": "4. 💾 Session & Memory",
        "memory_desc": "**Save your progress:**\nClick **💾 Download** to save history.",
        "memory_load": "📂 Resume previous session",
        "memory_save": "💾 Download Session",
        "reset": "🔄 New Session",
        "about": "📖 Project Philosophy",
        "about_text": "Groovebox Tutor helps you understand your gear instead of copying presets.",
        "support": "☕ Donate",
        "title": "Groovebox Tutor",
        "subtitle": "Your technical partner. Decode sound. Master your gear.",
        "placeholder": "Ask a question or let AI analyze...",
        "sugg_1": "Analyze sound",
        "sugg_2": "Rhythm structure",
        "sugg_3": "Hidden feature",
        "style_label": "Teaching Approach",
        "tones": ["🤙 Cool Mentor", "👔 Technical Expert", "⚡ Direct"],
        "formats": ["📝 Full Lesson", "✅ Checklist", "💬 Interactive"],
        "manual_loaded": "✅ Manual loaded",
        "active_track": "Active track:",
        "session_reloaded": "✅ Session reloaded!"
    }
}

# --- 4. FONCTIONS HELPER ---
def get_mime_type(filename):
    if filename.endswith('.m4a'): return 'audio/mp4'
    if filename.endswith('.wav'): return 'audio/wav'
    return 'audio/mp3'

def upload_pdf_to_gemini(path):
    try:
        file_ref = genai.upload_file(path=path, mime_type="application/pdf")
        while file_ref.state.name == "PROCESSING":
            time.sleep(1)
            file_ref = genai.get_file(file_ref.name)
        if file_ref.state.name == "FAILED": return None
        return file_ref
    except: return None

def format_history(history):
    text = f"SESSION {datetime.now().strftime('%Y-%m-%d')}\n---\n"
    for msg in history:
        role = "USER" if msg['role'] == "user" else "AI"
        text += f"{role}: {msg['content']}\n\n"
    return text

# --- 5. SYSTEM PROMPT (VERSION PROACTIVE) ---
def build_system_prompt(lang, style_tone, style_format, memory_context, has_manual, trigger_mode=None, user_level="Intermédiaire"):
    
    # Définition du niveau pédagogique
    if "Débutant" in user_level:
        level_instr = "NIVEAU DÉBUTANT : Vulgarise tout. N'utilise pas de jargon sans expliquer. Si le fichier audio est complexe (9mn+), propose de le découper."
    elif "Expert" in user_level:
        level_instr = "NIVEAU EXPERT : Sois concis. Donne directement les valeurs (0-127). Pas de blabla."
    else:
        level_instr = "NIVEAU INTERMÉDIAIRE : Guide l'utilisateur. Donne les réglages mais laisse-le tourner les boutons."

    manual_instruction = "Utilise le manuel comme référence. Cite les pages." if has_manual else "Explique les concepts généraux."
    
    base = f"""Tu es Groovebox Tutor. MISSION : Enseigner la synthèse sonore.
    STYLE : {level_instr}
    MANUEL : {manual_instruction}
    CONTEXTE : {memory_context}
    """
    
    if trigger_mode == "AUTO_ANALYSE":
        return base + """
        🔥 ANALYSE AUTO : L'utilisateur a chargé un son.
        1. Si c'est un MIX COMPLET (plusieurs instruments, long) : Ne donne pas de recette. Demande quel instrument isoler (Kick, Basse, Lead ?).
        2. Si c'est un SON SIMPLE : Donne le Diagnostic et la Recette Technique (Tableau).
        """
    elif trigger_mode == "AUTO_COACH":
        return base + "⚖️ COACHING : Compare l'essai et la cible. Donne une note /100 et une correction précise selon le niveau choisi."
    elif trigger_mode == "VISION":
        return base + "👀 VISION : Analyse la photo des réglages."
    else:
        return base + "Réponds à la question."

    TONE_PROFILES = {
        "🤙 Mentor Cool": {"voice": "Décontracté, tutoiement", "energy": "Enthousiaste"},
        "👔 Expert Technique": {"voice": "Professionnel, précis", "energy": "Rigoureux"},
        "⚡ Synthétique": {"voice": "Direct, efficace", "energy": "Minimaliste"},
        "🤙 Cool Mentor": {"voice": "Casual, encouraging", "energy": "Enthusiastic"},
        "👔 Technical Expert": {"voice": "Professional, precise", "energy": "Rigorous"},
        "⚡ Direct": {"voice": "Straight to the point", "energy": "Minimalist"}
    }
    
    tone = TONE_PROFILES.get(style_tone, TONE_PROFILES["🤙 Mentor Cool"])
    
    manual_instruction = "Utilise le manuel comme référence. Cite les pages." if has_manual else "Explique les concepts généraux."
    
    # Base du prompt
    base = f"""Tu es Groovebox Tutor, assistant technique proactif.
    
    MISSION : Aider l'utilisateur à maîtriser sa machine.
    STYLE : {tone['voice']} - {tone['energy']}. Format : {style_format}. Langue : {lang.split()[0]}.
    
    MANUEL : {manual_instruction}
    
    {memory_context}
    """
    
    # INSTRUCTIONS SPÉCIFIQUES SELON LE MODE (C'est ici que la magie opère)
    if trigger_mode == "AUTO_ANALYSE":
        return base + """
        🔥 MODE ANALYSE AUTOMATIQUE ACTIVÉ.
        L'utilisateur vient de charger un son. NE POSE PAS DE QUESTION.
        Fais immédiatement :
        1. 🎯 DIAGNOSTIC : Type de son, forme d'onde, texture.
        2. 🎛️ RECETTE TECHNIQUE (Tableau Markdown) :
           | Paramètre | Valeur |
           | OSC | ... |
           | FILTER | ... |
           | ENV | ... |
        3. 🚀 ACTION : Donne la première étape pour commencer.
        """
        
    elif trigger_mode == "AUTO_COACH":
        return base + """
        ⚖️ MODE COACHING AUTOMATIQUE ACTIVÉ.
        L'utilisateur vient d'envoyer son ESSAI.
        Fais immédiatement :
        1. 🏆 SCORE : Note la ressemblance sur 100.
        2. 📉 TABLEAU COMPARATIF :
           | Critère | Cible | Essai | Correction |
           | Timbre | ... | ... | ... |
           | Enveloppe| ... | ... | ... |
        3. 👮 VERDICT : Dis ce qu'il faut changer pour améliorer le score.
        """
        
    elif trigger_mode == "VISION":
        return base + """
        👀 MODE VISION.
        Analyse l'image fournie (réglages machine).
        Si un paramètre semble mal réglé par rapport au son voulu, dis-le.
        """
        
    else:
        return base + "Réponds à la question de l'utilisateur. Sois concis et technique."


# --- SIDEBAR ---
with st.sidebar:
    lang = st.selectbox("Langue / Language", list(TR.keys()), label_visibility="collapsed")
    T = TR.get(lang, TR["Français 🇫🇷"])
    
    # 1. CONFIGURATION
    st.markdown(f"### {T['settings']}")
    api_key = st.text_input(T["api_label"], type="password", placeholder="AIzaSy...")
    with st.expander(T["api_help"]):
        st.caption(T["api_desc"])

    st.markdown("---")
    
    # --- AJOUT PÉDAGOGIE (CORRIGÉ) ---
    st.markdown("### 🎓 Pédagogie")
    user_level = st.radio(
        "Ton Niveau", 
        ["Débutant", "Intermédiaire", "Expert"],
        index=1
    )
    # ---------------------------------
    
    st.markdown("---")

    # 2. FICHIERS
    st.markdown(f"### {T['doc_section']}")
    
    # Helper Manuels
    with st.expander(T["doc_help"]):
        MANUAL_LINKS = {
            "Elektron Digitakt II": "https://www.elektron.se/en/support-downloads/digitakt-ii",
            "Roland SP-404 MKII": "https://www.roland.com/global/products/sp-404mk2/support/",
            "TE EP-133 K.O. II": "https://teenage.engineering/downloads/ep-133",
            "Arturia MicroFreak": "https://www.arturia.com/products/hardware-synths/microfreak/resources"
        }
        machine = st.selectbox("Machine", list(MANUAL_LINKS.keys()), label_visibility="collapsed")
        st.link_button(f"⬇️ {machine}", MANUAL_LINKS[machine], use_container_width=True)
    
    # Upload 1 : Manuel PDF
    st.caption("📄 Manuel")
    uploaded_pdf = st.file_uploader(T["manual_upload"], type=["pdf"], label_visibility="collapsed", key="pdf_upload")
    if uploaded_pdf: st.success(T["manual_loaded"])
    
    # Upload 2 : Son Cible
    st.caption(T["audio_title"])
    uploaded_audio = st.file_uploader("Audio", type=["mp3", "wav", "m4a"], label_visibility="collapsed", key="audio_upload")
    
    # LOGIQUE D'UPLOAD AUDIO CIBLE & AUTO-TRIGGER
    if uploaded_audio:
        if "current_audio_name" not in st.session_state or st.session_state.current_audio_name != uploaded_audio.name:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                # 🔥 DÉCLENCHEUR PROACTIF
                st.session_state.auto_trigger = "ANALYSE"
                st.rerun()
    
    if "current_audio_path" in st.session_state:
        st.success(f"✅ {st.session_state.get('current_audio_name', 'Fichier')}")
        try:
            with open(st.session_state.current_audio_path, "rb") as f: st.audio(f.read())
        except: pass

    # --- MODE COACH ---
    st.markdown("---")
    st.markdown(f"### {T['coach_section']}")
    st.caption(T['coach_desc'])
    uploaded_try = st.file_uploader(T['coach_label'], type=["mp3", "wav", "m4a"], key="try_upload")
    
    # LOGIQUE D'UPLOAD ESSAI & AUTO-TRIGGER
    if uploaded_try:
        if "current_try_name" not in st.session_state or st.session_state.get("current_try_name") != uploaded_try.name:
             with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                t.write(uploaded_try.getvalue())
                st.session_state.try_path = t.name
                st.session_state.current_try_name = uploaded_try.name
                # 🔥 DÉCLENCHEUR PROACTIF
                st.session_state.auto_trigger = "COACH"
             st.success("✅ Essai prêt")
    
    # --- VISION DEBUG ---
    st.markdown("---")
    st.markdown(f"### {T['vision_section']}")
    st.caption(T['vision_desc'])
    
    img_mode = st.toggle(T['vision_toggle'])
    uploaded_img = None
    
    if img_mode:
        tab_cam, tab_upl = st.tabs(["📸 Caméra", "📂 Fichier"])
        with tab_cam:
            cam_pic = st.camera_input("Photo")
            if cam_pic: uploaded_img = cam_pic
        with tab_upl:
            upl_pic = st.file_uploader("Image", type=["jpg", "png", "jpeg"])
            if upl_pic: uploaded_img = upl_pic
            
    if uploaded_img:
        st.image(uploaded_img, width=220)
        img_data = Image.open(uploaded_img)
        st.session_state.vision_ref = img_data

    st.markdown("---")
    
    # 3. STYLE PÉDAGOGIQUE
    st.markdown(f"### {T['style_section']}")
    style_tone = st.selectbox("Ton", T["tones"], index=0, label_visibility="collapsed")
    style_format = st.radio("Format", T["formats"], index=0, label_visibility="collapsed")

    st.markdown("---")
    
    # Session Management
    with st.expander("💾 " + T["memory_load"]):
        uploaded_memory = st.file_uploader("Session .txt", type=["txt"], key="mem_upload")
        if uploaded_memory:
            st.session_state.memory_content = uploaded_memory.getvalue().decode("utf-8")
            st.success(T["session_reloaded"])

    if "chat_history" in st.session_state and st.session_state.chat_history:
        col_dl, col_reset = st.columns(2)
        with col_dl:
            st.download_button("💾", format_history(st.session_state.chat_history), "session.txt", use_container_width=True, type="primary")
        with col_reset:
            if st.button("🔄", use_container_width=True, type="secondary"):
                st.session_state.clear()
                st.rerun()
    
    with st.expander(T["about"]):
        st.markdown(T["about_text"])
        st.markdown(f"[{T['support']}](https://www.buymeacoffee.com/)")

# --- MAIN AREA ---
st.title(T["title"])
st.markdown(f"<h3 style='margin-top: -20px; margin-bottom: 40px; color: #808080;'>{T['subtitle']}</h3>", unsafe_allow_html=True)

# --- LOGIC V4.0 (GEMINI 2.0 FLASH + PROACTIVITÉ TOTALE) ---
if api_key:
    genai.configure(api_key=api_key)
    
    # 1. GESTION DU PDF
    if uploaded_pdf:
        if "current_pdf_name" not in st.session_state or st.session_state.current_pdf_name != uploaded_pdf.name:
            with st.status("Traitement du manuel...", expanded=False) as status:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
                    t.write(uploaded_pdf.getvalue())
                    p = t.name
                r = upload_pdf_to_gemini(p)
                if r: 
                    st.session_state.pdf_ref = r
                    st.session_state.current_pdf_name = uploaded_pdf.name
                    status.update(label="✅ Manuel assimilé", state="complete")

    # 2. GESTION AUDIO CIBLE (Upload Gemini)
    if "current_audio_path" in st.session_state:
        if "audio_ref" not in st.session_state or st.session_state.get("last_uploaded_audio") != st.session_state.current_audio_name:
             with st.status("Analyse du son cible...", expanded=False) as status:
                try:
                    audio_file_ref = genai.upload_file(path=st.session_state.current_audio_path)
                    while audio_file_ref.state.name == "PROCESSING":
                        time.sleep(0.5)
                        audio_file_ref = genai.get_file(audio_file_ref.name)
                    st.session_state.audio_ref = audio_file_ref
                    st.session_state.last_uploaded_audio = st.session_state.current_audio_name
                    status.update(label="✅ Audio Cible prêt", state="complete")
                except Exception as e: st.error(f"Erreur Audio: {e}")

    # 3. GESTION AUDIO ESSAI (Upload Gemini)
    if "try_path" in st.session_state:
        if "try_ref" not in st.session_state or st.session_state.get("last_uploaded_try") != st.session_state.current_try_name:
             with st.spinner("L'IA écoute votre essai..."):
                try:
                    tr_ref = genai.upload_file(path=st.session_state.try_path)
                    while tr_ref.state.name == "PROCESSING":
                        time.sleep(0.5)
                        tr_ref = genai.get_file(tr_ref.name)
                    st.session_state.try_ref = tr_ref
                    st.session_state.last_uploaded_try = st.session_state.current_try_name
                    st.toast("✅ Essai reçu !")
                except: pass

    # 4. AFFICHAGE HISTORIQUE (Doit être AVANT les inputs pour ne pas clignoter)
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # --- LOGIQUE DES DÉCLENCHEURS ---
    prompt = None
    # On récupère le trigger défini lors de l'upload (ANALYSE ou COACH)
    trigger = st.session_state.get("auto_trigger") 

    if trigger == "ANALYSE":
        prompt = "🔥 [AUTO] Analyse ce son. Attention à la durée du fichier."
        with st.chat_message("user"): st.markdown("🎵 *Audio chargé... Analyse en cours*")
        st.session_state.chat_history.append({"role": "user", "content": "🎵 *Audio chargé... Analyse en cours*"})
        st.session_state.auto_trigger = None # On reset le trigger

    elif trigger == "COACH":
        prompt = "⚖️ [AUTO] Note mon essai sur 100."
        with st.chat_message("user"): st.markdown("🧪 *Essai envoyé pour correction*")
        st.session_state.chat_history.append({"role": "user", "content": "🧪 *Essai envoyé pour correction*"})
        st.session_state.auto_trigger = None

    else:
        # Input manuel (si pas de trigger auto)
        user_input = st.chat_input(T["placeholder"])
        if user_input:
            prompt = user_input
            with st.chat_message("user"): st.markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

    # 5. GÉNÉRATION IA
    if prompt:
        with st.chat_message("assistant"):
            with st.spinner("Réflexion..."):
                try:
                    # Contexte
                    req = []
                    if "pdf_ref" in st.session_state: req.extend([st.session_state.pdf_ref, "MANUEL"])
                    if "audio_ref" in st.session_state: req.extend([st.session_state.audio_ref, "SON CIBLE"])
                    if "try_ref" in st.session_state: req.extend([st.session_state.try_ref, "ESSAI"])
                    if "vision_ref" in st.session_state: req.extend([st.session_state.vision_ref, "PHOTO"])
                    req.append(prompt)

                    # Prompt intelligent
                    sys_prompt = build_system_prompt(
                        lang, style_tone, style_format, 
                        st.session_state.get("memory_content", ""), 
                        "pdf_ref" in st.session_state,
                        trigger_mode=trigger if trigger else "VISION" if "vision_ref" in st.session_state else None,
                        user_level=user_level # On passe le niveau choisi
                    )

                    # Appel Gemini 2.0
                    model = genai.GenerativeModel("gemini-2.0-flash-exp", system_instruction=sys_prompt)
                    resp = model.generate_content(req)
                    
                    st.markdown(resp.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
                except Exception as e:
                    st.error(f"Erreur : {e}")

else:
    st.sidebar.warning("⚠️ Clé API requise")