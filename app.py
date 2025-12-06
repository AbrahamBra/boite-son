import streamlit as st
import google.generativeai as genai
import os
import tempfile
import time
import pathlib
import re
from datetime import datetime
from PIL import Image  # <--- AJOUT CRUCIAL POUR LA VISION

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
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 3rem; padding-bottom: 5rem;}
    
    /* Info Box */
    div[data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.05); border: 1px solid #303030; color: #E0E0E0; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DICTIONNAIRE COMPLET (AVEC AJOUTS V3) ---
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
        # --- AJOUTS V3 ---
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
- 👁️ Elle regarde vos réglages (Vision)
- 🎛️ Elle vous guide pour **recréer** le son par vous-même

Pas de preset tout fait. Pas de solution miracle. Juste de la **pédagogie**, étape par étape.

### Pourquoi c'est gratuit ?

Parce que la connaissance doit être accessible. Ce projet est open-source et le restera. Si vous progressez grâce à lui, un café virtuel fait toujours plaisir ☕

*Fait avec ❤️ pour les beatmakers, les sound designers, et tous ceux qui refusent de rester en surface.*""",
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
        "session_reloaded": "✅ Session rechargée ! L'IA se souvient du contexte."
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
        # --- AJOUTS V3 ---
        "coach_section": "🧪 Coach Mode (Comparison)",
        "coach_desc": "Upload your attempt here. AI will compare it with the target.",
        "coach_label": "My Attempt (mp3/wav)",
        "vision_section": "👁️ Vision Debug",
        "vision_desc": "Show your settings (Photo)",
        "vision_toggle": "Enable Camera / Upload",
        # -----------------
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
- 👁️ It looks at your settings
- 🎛️ It guides you to **recreate** the sound yourself

No ready-made presets. No magic solution. Just **pedagogy**, step by step.

### Why is it free?

Because knowledge should be accessible. This project is open-source and will stay that way. If you progress thanks to it, a virtual coffee is always appreciated ☕

*Made with ❤️ for beatmakers, sound designers, and everyone who refuses to stay on the surface.*""",
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
        "session_reloaded": "✅ Session reloaded! The AI remembers the context."
    }
}
# --- 4. FONCTIONS ---
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

def build_system_prompt(lang, style_tone, style_format, memory_context, has_manual):
    
    TONE_PROFILES = {
        "🤙 Mentor Cool": {"voice": "Décontracté, tutoiement", "energy": "Enthousiaste"},
        "👔 Expert Technique": {"voice": "Professionnel, précis", "energy": "Rigoureux"},
        "⚡ Synthétique": {"voice": "Direct, efficace", "energy": "Minimaliste"},
        "🤙 Cool Mentor": {"voice": "Casual, encouraging", "energy": "Enthusiastic"},
        "👔 Technical Expert": {"voice": "Professional, precise", "energy": "Rigorous"},
        "⚡ Direct": {"voice": "Straight to the point", "energy": "Minimalist"}
    }
    
    FORMAT_PROFILES = {
        "📝 Cours Complet": "Explications détaillées",
        "✅ Checklist": "Étapes numérotées",
        "💬 Interactif": "Dialogue naturel",
        "📝 Full Lesson": "Detailed explanations",
        "✅ Checklist": "Numbered steps",
        "💬 Interactive": "Natural dialogue"
    }
    
    tone = TONE_PROFILES.get(style_tone, TONE_PROFILES["🤙 Mentor Cool"])
    fmt = FORMAT_PROFILES.get(style_format, FORMAT_PROFILES["📝 Cours Complet"])
    
    manual_instruction = "Utilise le manuel comme référence. Cite les pages." if has_manual else "Explique les concepts généraux."
    
    # PROMPT ÉTENDU POUR V3
    return f"""Tu es Groovebox Tutor, assistant technique pour groovebox.

MISSION : Aider l'utilisateur à maîtriser sa machine et composer les sons qu'il veut.

STYLE :
- Ton : {tone['voice']} - {tone['energy']}
- Format : {fmt}
- Langue : {lang.split()[0]}

{memory_context}

MANUEL : {manual_instruction}

RÈGLES D'ANALYSE ET RÉPONSE :

1. AUDIO CIBLE SEUL : 
   - Analyse le spectre, le timbre, les effets.
   - Explique comment recréer ce son (synthèse, sampling).

2. AUDIO CIBLE + ESSAI (Mode Coach) :
   - Compare les deux fichiers.
   - Dis ce qui est bien dans l'essai.
   - Dis ce qu'il faut corriger (ADSR, Filtre, Pitch) pour coller à la cible.

3. VISION (Image fournie) :
   - Analyse la photo de la machine.
   - Regarde la position des potentiomètres, l'écran ou les câbles.
   - Utilise ces indices pour debugger le problème (ex: "Ton filtre est fermé à fond, ouvre-le").

NE FAIS JAMAIS :
- Poser des questions type "Qu'en penses-tu ?"
- Donner des valeurs exactes arbitraires (ex: Cutoff=63) sans expliquer.
- Fournir un preset clé-en-main sans explication.

FAIS TOUJOURS :
- Répondre directement.
- Expliquer le pourquoi technique.

CONNAISSANCES : Synthèse (soustractive, FM, wavetable), Machines (Elektron, MPC, SP-404, OP-1), Signal (filtres, ADSR, LFO), Effets (reverb, delay, distortion)

ÉTHIQUE : Outil éducatif. Apprendre les techniques, pas copier des presets.

Prêt à aider !"""

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
    
    # 2. FICHIERS (tout regroupé)
    st.markdown(f"### {T['doc_section']}")
    
    # Helper pour trouver les manuels
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
    st.caption("📄 Manuel de votre machine" if lang == "Français 🇫🇷" else "📄 Your gear manual")
    uploaded_pdf = st.file_uploader(
        "Manuel PDF", 
        type=["pdf"], 
        label_visibility="collapsed",
        key="pdf_upload"
    )
    if uploaded_pdf:
        st.success(T["manual_loaded"])
    
    # Upload 2 : Son à analyser
    st.caption("🎵 Son à analyser" if lang == "Français 🇫🇷" else "🎵 Sound to analyze")
    uploaded_audio = st.file_uploader(
        "Audio", 
        type=["mp3", "wav", "m4a"], 
        label_visibility="collapsed",
        key="audio_upload"
    )
    
    # Gestion Audio Cible (Sécurisée)
    if uploaded_audio:
        if "current_audio_name" not in st.session_state or st.session_state.current_audio_name != uploaded_audio.name:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                st.rerun()
    
    if "current_audio_path" in st.session_state:
        st.success(f"✅ {st.session_state.get('current_audio_name', 'Fichier Audio')}")
        
        # CORRECTION : On lit les bytes directement pour éviter l'erreur MediaFileStorage
        try:
            with open(st.session_state.current_audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            st.audio(audio_bytes)
        except FileNotFoundError:
            st.warning("⚠️ Le fichier audio a expiré. Merci de le recharger.")
            del st.session_state.current_audio_path
            st.rerun()
            
    # --- NOUVEAU : MODE COACH ---
    st.markdown("---")
    st.markdown(f"### {T['coach_section']}")
    st.caption(T['coach_desc'])
    
    uploaded_try = st.file_uploader(
        T['coach_label'], 
        type=["mp3", "wav", "m4a"], 
        key="try_upload"
    )
    
    # Gestion Audio Essai (Sécurisée)
    if uploaded_try:
        if "current_try_name" not in st.session_state or st.session_state.get("current_try_name") != uploaded_try.name:
             with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                t.write(uploaded_try.getvalue())
                st.session_state.try_path = t.name
                st.session_state.current_try_name = uploaded_try.name
             st.success("✅ Essai prêt")
    
    # --- NOUVEAU : VISION DEBUG ---
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
    
    # Upload 3 : Session précédente
    with st.expander("💾 " + ("Reprendre une session" if lang == "Français 🇫🇷" else "Resume session")):
        st.caption(T["memory_desc"])
        uploaded_memory = st.file_uploader(
            "Session .txt", 
            type=["txt"], 
            label_visibility="collapsed",
            key="mem_upload"
        )
        if uploaded_memory:
            st.session_state.memory_content = uploaded_memory.getvalue().decode("utf-8")
            st.success(T["session_reloaded"])

    st.markdown("---")
    
    # 3. STYLE PÉDAGOGIQUE
    st.markdown(f"### {T['style_section']}")
    style_tone = st.selectbox("Ton", T["tones"], index=0, label_visibility="collapsed")
    style_format = st.radio("Format", T["formats"], index=0, label_visibility="collapsed")

    st.markdown("---")
    
    # FOOTER : ACTIONS (seulement si une conversation existe)
    if "chat_history" in st.session_state and st.session_state.chat_history:
        history_txt = format_history(st.session_state.chat_history)
        
        col_dl, col_reset = st.columns(2)
        
        with col_dl:
            st.download_button(
                "💾",
                history_txt, 
                f"groovebox_session_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", 
                "text/plain", 
                use_container_width=True,
                type="primary",
                help=T["memory_save"]
            )
        
        with col_reset:
            if st.button(
                "🔄",
                use_container_width=True,
                type="secondary",
                help=T["reset"]
            ):
                st.session_state.clear()
                st.rerun()
    
    # Footer philosophie (toujours visible)
    with st.expander(T["about"]):
        st.markdown(T["about_text"])
        st.markdown(f"[{T['support']}](https://www.buymeacoffee.com/)")

# --- MAIN AREA ---
st.title(T["title"])
st.markdown(f"<h3 style='margin-top: -20px; margin-bottom: 40px; color: #808080;'>{T['subtitle']}</h3>", unsafe_allow_html=True)

# --- LOGIC V3.0 (INTEGRALE : GEMINI 2.0 + VISION + COACH) ---
if api_key:
    genai.configure(api_key=api_key)
    
    # 1. GESTION DU PDF (Manuel)
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

    # 2. GESTION DE L'AUDIO PRINCIPAL (Cible)
    if "current_audio_path" in st.session_state:
        if "audio_ref" not in st.session_state or st.session_state.get("last_uploaded_audio") != st.session_state.current_audio_name:
             with st.status("Analyse du son cible...", expanded=False) as status:
                try:
                    # Upload vers Gemini (Indispensable)
                    audio_file_ref = genai.upload_file(path=st.session_state.current_audio_path)
                    
                    # Attente processing
                    while audio_file_ref.state.name == "PROCESSING":
                        time.sleep(0.5)
                        audio_file_ref = genai.get_file(audio_file_ref.name)
                        
                    st.session_state.audio_ref = audio_file_ref
                    st.session_state.last_uploaded_audio = st.session_state.current_audio_name
                    status.update(label="✅ Audio Cible prêt", state="complete")
                except Exception as e:
                    st.error(f"Erreur upload audio : {e}")

    # 3. FEATURE COACH : UPLOAD DE L'ESSAI
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
                    st.toast("✅ Essai reçu ! Prêt pour le coaching.")
                except Exception as e: 
                    st.error(f"Erreur : {e}")

    # 4. AFFICHAGE HISTORIQUE CHAT
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # 5. INPUT USER
    prompt = None
    if not st.session_state.chat_history:
        col1, col2, col3 = st.columns(3)
        if col1.button(T["sugg_1"], type="secondary", use_container_width=True): prompt = T["sugg_1"]
        elif col2.button(T["sugg_2"], type="secondary", use_container_width=True): prompt = T["sugg_2"]
        elif col3.button(T["sugg_3"], type="secondary", use_container_width=True): prompt = T["sugg_3"]

    user_input = st.chat_input(T["placeholder"])
    if user_input:
        prompt = user_input

    # 6. GÉNÉRATION INTELLIGENTE (GEMINI 2.0 FLASH)
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Outils
        tools = None 
        
        # Contexte Mémoire
        memory_context = ""
        if "memory_content" in st.session_state:
            memory_context = f"## CONTEXTE MEMOIRE\n{st.session_state.memory_content}\n"

        sys_prompt = build_system_prompt(
            lang=lang,
            style_tone=style_tone,
            style_format=style_format,
            memory_context=memory_context,
            has_manual="pdf_ref" in st.session_state
        )
        
        # --- CIBLAGE MODÈLE : GEMINI 2.0 FLASH ---
        target_model = "gemini-2.0-flash-exp"
        try:
            model = genai.GenerativeModel(target_model, system_instruction=sys_prompt, tools=tools)
        except:
            # Fallback Sécurité
            model = genai.GenerativeModel("gemini-1.5-pro", system_instruction=sys_prompt)

        # Construction de la requête Multimodale
        req = []
        
        # A. Manuel
        if "pdf_ref" in st.session_state:
            req.append(st.session_state.pdf_ref)
            req.append("MANUEL TECHNIQUE (Référence).")
            
        # B. Audio Cible (L'objectif)
        if "audio_ref" in st.session_state:
            req.append(st.session_state.audio_ref)
            req.append("SON CIBLE (Reference Audio). Analyse ce son.")
            
        # C. Audio Essai (Mode Coach)
        if "try_ref" in st.session_state:
            req.append(st.session_state.try_ref)
            req.append("SON ESSAI (User Attempt). C'est ce que j'ai produit.")
            prompt += "\n\n⚠️ [INSTRUCTION COACH] : Compare mon ESSAI avec la CIBLE. Dis ce qui manque (Filtre ? Enveloppe ? Effet ?) pour que l'essai sonne comme la cible."

        # D. Vision (Debug Photo)
        if "vision_ref" in st.session_state:
            req.append(st.session_state.vision_ref)
            req.append("PHOTO DE LA MACHINE : Analyse les réglages visibles (boutons, écran).")
            prompt += "\n\n👀 [VISION] : Regarde la photo de ma machine. Est-ce que mes réglages semblent cohérents avec le son que je veux ?"

        # E. La Question
        req.append(prompt)

        with st.chat_message("assistant"):
            with st.spinner(f"Analyse neurale ({target_model})..."):
                try:
                    resp = model.generate_content(req)
                    text_resp = resp.text
                    
                    # Indicateur visuel discret
                    if "2.0" in target_model:
                        st.caption(f"⚡ Propulsé par {target_model}")
                        
                    st.markdown(text_resp)
                    st.session_state.chat_history.append({"role": "assistant", "content": text_resp})
                except Exception as e:
                    st.error(f"Erreur IA : {e}")

else:
    st.sidebar.warning("⚠️ Clé API requise / API Key needed")