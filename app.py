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

# --- 2. CSS PREMIUM (DESIGN COMPLET) ---
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
    .stChatMessage { background-color: rgba(255, 255, 255, 0.02); border: 1px solid #333; border-radius: 12px; margin-bottom: 10px; }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 3rem; padding-bottom: 5rem;}
    
    /* Info Box */
    div[data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.05); border: 1px solid #303030; color: #E0E0E0; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DICTIONNAIRE COMPLET (AVEC TEXTES RICHES & CORRECTIONS) ---
TR = {
    "Français 🇫🇷": {
        "settings": "1. Configuration",
        "api_label": "Clé API Google",
        "api_help": "ℹ️ Pourquoi une clé perso ?",
        "api_desc": "Projet open-source. L'usage de votre propre clé gratuite garantit votre indépendance et la gratuité totale de l'outil.",
        "doc_section": "2. Votre Machine",
        "doc_help": "🔍 Trouver mon manuel officiel",
        "manual_upload": "Déposer le Manuel PDF ici",
        "audio_title": "🎧 Le Son à Analyser",
        "audio_subtitle": "C'est ici que la magie opère. Glissez un fichier pour lancer l'écoute.",
        "audio_label": "Fichier Audio",
        # --- AJOUTS V5 ---
        "coach_section": "🧪 Mode Coach (Comparaison)",
        "coach_desc": "Charge ton propre essai ici. L'IA comparera ton son avec la cible.",
        "coach_label": "Mon Essai (mp3/wav)",
        "vision_section": "👁️ Vision Debug",
        "vision_desc": "Montre tes réglages (Photo)",
        "vision_toggle": "Activer Caméra / Upload",
        # -----------------
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

Pas de preset tout fait. Pas de solution miracle. Juste de la **pédagogie**, étape par étape.

### Pourquoi c'est gratuit ?

Parce que la connaissance doit être accessible. Ce projet est open-source et le restera. Si vous progressez grâce à lui, un café virtuel fait toujours plaisir ☕""",
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
        "about_text": "Groovebox Tutor helps you understand your gear instead of copying presets.",
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

def build_system_prompt(lang, style_tone, style_format, memory_context, has_manual, trigger_mode=None, user_level="Intermédiaire"):
    
    TONE_PROFILES = {
        "🤙 Mentor Cool": {"voice": "Décontracté, tutoiement", "energy": "Enthousiaste"},
        "👔 Expert Technique": {"voice": "Professionnel, précis", "energy": "Rigoureux"},
        "⚡ Synthétique": {"voice": "Direct, efficace", "energy": "Minimaliste"},
        "🤙 Cool Mentor": {"voice": "Casual, encouraging", "energy": "Enthusiastic"},
        "👔 Technical Expert": {"voice": "Professional, precise", "energy": "Rigorous"},
        "⚡ Direct": {"voice": "Straight to the point", "energy": "Minimalist"}
    }
    
    tone = TONE_PROFILES.get(style_tone, TONE_PROFILES["🤙 Mentor Cool"])
    
    # 1. GESTION DES NIVEAUX (PÉDAGOGIE)
    if "Débutant" in user_level:
        level_instr = """
        NIVEAU DÉBUTANT ABSOLU : Tuto "Bouton par Bouton".
        L'utilisateur ne connait pas la machine. Ne parle pas de théorie (pas de "nappes", "ambiances").
        GUIDE-LE PHYSIQUEMENT sur la machine.
        Exemple attendu : "1. Sélectionne la piste 1. 2. Appuie sur le bouton AMP. 3. Tourne le bouton A vers la droite."
        Utilise le manuel pour nommer les boutons EXACTS.
        """
    elif "Expert" in user_level:
        level_instr = "NIVEAU EXPERT : Valeurs brutes (0-127), jargon technique précis, pas d'explications superflues. Donne un tableau de patch."
    else:
        level_instr = "NIVEAU INTERMÉDIAIRE : Guide l'utilisateur sur la structure du son et les modules à utiliser."

    manual_instruction = "Utilise le manuel comme BIBLE ABSOLUE. Cite les pages." if has_manual else "Explique les concepts généraux."
    
    base = f"""Tu es Groovebox Tutor.
    MISSION : Guider l'utilisateur sur sa machine physique.
    STYLE : {tone['voice']} - {tone['energy']}.
    NIVEAU PÉDAGOGIQUE : {level_instr}
    MANUEL : {manual_instruction}
    
    CONTEXTE : {memory_context}
    """
    
    # 2. GESTION DES TRIGGERS (PROACTIVITÉ)
    if trigger_mode == "AUTO_ANALYSE":
        return base + """
        🔥 ACTION : Analyse le son chargé.
        1. Si le son est LONG (> 30s) ou complexe : NE DONNE PAS DE RECETTE GLOBALE.
           Dis : "C'est un morceau complet. Choisis un élément pour commencer : 1. Kick, 2. Basse, 3. Nappe ?"
        2. Si le son est COURT : Donne la procédure pas à pas (selon le niveau choisi) pour le refaire.
        """
    elif trigger_mode == "AUTO_COACH":
        return base + "⚖️ ACTION : Note l'essai sur 100 et dis quel bouton tourner pour corriger l'écart."
    elif trigger_mode == "VISION":
        return base + "👀 ACTION : Regarde la photo. Est-ce que les réglages sont cohérents avec le son voulu ?"
    else:
        return base + "Réponds à la question."

# --- 5. INTERFACE ---

# --- SIDEBAR ---
with st.sidebar:
    lang = st.selectbox("Langue / Language", list(TR.keys()), label_visibility="collapsed")
    T = TR.get(lang, TR["Français 🇫🇷"])
    
    # 1. CONFIGURATION
    st.markdown(f"### {T['settings']}")
    api_key = st.text_input(T["api_label"], type="password", placeholder="AIzaSy...")
    with st.expander(T["api_help"]):
        st.caption(T["api_desc"])
        st.markdown("[Google AI Studio](https://aistudio.google.com/) (Free)")

    st.markdown("---")
    
    # --- AJOUT PÉDAGOGIE (NOUVEAU) ---
    st.markdown("### 🎓 Pédagogie")
    user_level = st.radio(
        "Ton Niveau", 
        ["Débutant (Pas à pas)", "Intermédiaire (Guide)", "Expert (Valeurs)"],
        index=0
    )
    # ---------------------------------
    
    st.markdown("---")
    
    # 2. FICHIERS
    st.markdown(f"### {T['doc_section']}")
    
    # Helper Manuels (CONSERVÉ)
    with st.expander(T["doc_help"]):
        MANUAL_LINKS = {
            "Elektron Digitakt II": "https://www.elektron.se/en/support-downloads/digitakt-ii",
            "Roland SP-404 MKII": "https://www.roland.com/global/products/sp-404mk2/support/",
            "TE EP-133 K.O. II": "https://teenage.engineering/downloads/ep-133",
            "Korg Volca Sample 2": "https://www.korg.com/us/support/download/product/0/867/",
            "Akai MPC One/Live": "https://www.akaipro.com/mpc-one",
            "Novation Circuit Tracks": "https://downloads.novationmusic.com/novation/circuit/circuit-tracks",
            "Arturia MicroFreak": "https://www.arturia.com/products/hardware-synths/microfreak/resources"
        }
        machine = st.selectbox("Machine", list(MANUAL_LINKS.keys()), label_visibility="collapsed")
        st.link_button(f"⬇️ {machine}", MANUAL_LINKS[machine], use_container_width=True)
    
    # Upload 1 : Manuel PDF
    st.caption(f"📄 {T['manual_upload']}")
    uploaded_pdf = st.file_uploader(
        "Manuel PDF", 
        type=["pdf"], 
        label_visibility="collapsed",
        key="pdf_upload"
    )
    if uploaded_pdf: st.success(T["manual_loaded"])
    
    # Upload 2 : Son à analyser
    st.caption(f"🎵 {T['audio_label']}")
    uploaded_audio = st.file_uploader(
        "Audio", 
        type=["mp3", "wav", "m4a"], 
        label_visibility="collapsed",
        key="audio_upload"
    )
    
    # LOGIQUE D'UPLOAD AUDIO CIBLE & AUTO-TRIGGER
    if uploaded_audio:
        if "current_audio_name" not in st.session_state or st.session_state.current_audio_name != uploaded_audio.name:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                # 🔥 DÉCLENCHEUR PROACTIF
                st.session_state.auto_trigger = "AUTO_ANALYSE"
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
    
    uploaded_try = st.file_uploader(
        T['coach_label'], 
        type=["mp3", "wav", "m4a"], 
        key="try_upload"
    )
    
    # LOGIQUE D'UPLOAD ESSAI & AUTO-TRIGGER
    if uploaded_try:
        if "current_try_name" not in st.session_state or st.session_state.get("current_try_name") != uploaded_try.name:
             with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                t.write(uploaded_try.getvalue())
                st.session_state.try_path = t.name
                st.session_state.current_try_name = uploaded_try.name
                # 🔥 DÉCLENCHEUR PROACTIF
                st.session_state.auto_trigger = "AUTO_COACH"
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
        st.toast("👀 L'IA voit tes réglages !")

    st.markdown("---")
    
    # 3. STYLE & MEMOIRE
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
            st.download_button(
                "💾", 
                format_history(st.session_state.chat_history), 
                f"groovebox_session_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                "text/plain", 
                use_container_width=True, 
                type="primary"
            )
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

# --- LOGIC V5.0 (GEMINI 2.0 FLASH + PROACTIVITÉ + NO BUGS) ---
if api_key:
    genai.configure(api_key=api_key)
    
    # 0. INITIALISATION CHAT
    if "chat_history" not in st.session_state: st.session_state.chat_history = []

    # --- CORRECTION BUG : AFFICHAGE DU CHAT EN PREMIER (STABLE) ---
    chat_container = st.container()
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    # 1. GESTION DES UPLOADS EN ARRIÈRE-PLAN
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.status("Lecture Manuel...", expanded=False):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
                t.write(uploaded_pdf.getvalue()); path=t.name
            ref = genai.upload_file(path, mime_type="application/pdf")
            while ref.state.name == "PROCESSING": time.sleep(1); ref = genai.get_file(ref.name)
            st.session_state.pdf_ref = ref

    if "current_audio_path" in st.session_state and "audio_ref" not in st.session_state:
        with st.status("Analyse Audio...", expanded=False):
            ref = genai.upload_file(path=st.session_state.current_audio_path)
            while ref.state.name == "PROCESSING": time.sleep(0.5); ref = genai.get_file(ref.name)
            st.session_state.audio_ref = ref

    if "try_path" in st.session_state and "try_ref" not in st.session_state:
        with st.status("Analyse Essai...", expanded=False):
            ref = genai.upload_file(path=st.session_state.try_path)
            while ref.state.name == "PROCESSING": time.sleep(0.5); ref = genai.get_file(ref.name)
            st.session_state.try_ref = ref

    # 2. GESTION DES TRIGGERS & INPUT
    prompt = None
    trigger = st.session_state.get("auto_trigger") # CORRECTION NOM VARIABLE

    if trigger == "AUTO_ANALYSE":
        prompt = "🔥 [AUTO] Analyse ce fichier. Guide-moi selon mon niveau."
        # Pas d'ajout user immédiat pour éviter doublon
        st.session_state.auto_trigger = None

    elif trigger == "AUTO_COACH":
        prompt = "⚖️ [AUTO] J'ai envoyé mon essai. Corrige-moi."
        st.session_state.auto_trigger = None
    
    else:
        # Suggestion Buttons
        if not st.session_state.chat_history:
            col1, col2, col3 = st.columns(3)
            if col1.button(T["sugg_1"], use_container_width=True): prompt = T["sugg_1"]
            elif col2.button(T["sugg_2"], use_container_width=True): prompt = T["sugg_2"]
            elif col3.button(T["sugg_3"], use_container_width=True): prompt = T["sugg_3"]

        user_input = st.chat_input(T["placeholder"])
        if user_input: prompt = user_input
        
        # Si un prompt manuel est détecté
        if prompt:
            with chat_container:
                with st.chat_message("user"): st.markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

    # 3. GÉNÉRATION IA
    if prompt:
        # On affiche un spinner DANS le container du chat
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(T["analyzing"]): # Utilisation de la clé T corrigée
                    try:
                        req = []
                        if "pdf_ref" in st.session_state: req.extend([st.session_state.pdf_ref, "MANUEL"])
                        if "audio_ref" in st.session_state: req.extend([st.session_state.audio_ref, "CIBLE"])
                        if "try_ref" in st.session_state: req.extend([st.session_state.try_ref, "ESSAI"])
                        if "vision_ref" in st.session_state: req.extend([st.session_state.vision_ref, "PHOTO"])
                        req.append(prompt)
                        
                        sys_prompt = build_system_prompt(
                            lang, style_tone, style_format, 
                            st.session_state.get("memory_content", ""), 
                            "pdf_ref" in st.session_state,
                            trigger_mode="AUTO_ANALYSE" if trigger == "AUTO_ANALYSE" else "AUTO_COACH" if trigger == "AUTO_COACH" else None,
                            user_level=user_level
                        )

                        # Modele Flash 2.0 (Le plus rapide et stable)
                        model = genai.GenerativeModel("gemini-2.0-flash-exp", system_instruction=sys_prompt)
                        resp = model.generate_content(req)
                        
                        st.markdown(resp.text)
                        st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
                    except Exception as e:
                        st.error(f"Erreur : {e}")

else:
    st.sidebar.warning("⚠️ Clé API requise / API Key needed")