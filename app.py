import streamlit as st
import google.generativeai as genai
import os
import tempfile
import time
import pathlib
import re
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS PREMIUM ---
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

# --- 3. DICTIONNAIRE RICHE (LE VRAI TEXTE) ---
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
        "memory_title": "Options Avancées (Mémoire)",
        "memory_load": "Reprendre une session (.txt)",
        "memory_save": "Sauvegarder Session",
        "reset": "Nouvelle Session",
        "about": "Philosophie du projet",
        # LE TEXTE RICHE EST DE RETOUR ICI :
        "about_text": "**Groovebox Tutor** est un projet libre, né du désir de reconnecter les musiciens avec leurs machines.\n\nNotre but n'est pas de copier, mais de **comprendre**. L'IA agit comme un binôme technique : elle écoute, lit la doc, et vous explique *comment* sculpter votre propre son.\n\nL'outil est gratuit. Si vous apprenez des choses grâce à lui, vous pouvez soutenir son maintien.",
        "support": "Soutenir (Don)",
        "title": "Groovebox Tutor",
        "subtitle": "Votre binôme technique. Décryptez le son. Maîtrisez votre machine.",
        "placeholder": "Posez une question technique sur ce son...",
        # L'ONBOARDING PEDAGOGIQUE EST DE RETOUR ICI :
        "onboarding": "👋 **Objectif : Autonomie**\n1. Importez le **Manuel** de votre instrument (à gauche).\n2. Proposez un **Son** qui vous inspire (ci-dessous).\n3. Votre binôme analyse la texture et vous enseigne **les étapes techniques** pour recréer ce grain vous-même.",
        "legal": "⚠️ Outil d'analyse à but éducatif. L'inspiration est légale, le plagiat ne l'est pas.",
        "sugg_1": "Analyse ce son",
        "sugg_2": "Structure rythmique",
        "sugg_3": "Fonction cachée",
        "style_label": "Approche Pédagogique",
        "tones": ["🤙 Mentor Cool", "👔 Expert Technique", "⚡ Synthétique"],
        "formats": ["📝 Cours Complet", "✅ Checklist", "💬 Interactif"],
        "manual_loaded": "✅ Manuel assimilé",
        "active_track": "Piste active :"
    },
    # (Je garde l'Anglais pour la structure, les autres langues suivront ce modèle riche si tu les déploies)
    "English 🇬🇧": {"settings": "1. Setup", "api_label": "Google API Key", "api_help": "Why a personal key?", "api_desc": "Open-source project. Using your own free key ensures your independence.", "doc_section": "2. Your Gear", "doc_help": "Find official manual", "manual_upload": "Drop PDF Manual here", "audio_title": "🎧 The Sound", "audio_subtitle": "Magic happens here. Drop your audio file.", "audio_label": "Audio File", "memory_title": "Advanced (Memory)", "memory_load": "Load Session", "memory_save": "Save Session", "reset": "New Session", "about": "Project Philosophy", "about_text": "**Groovebox Tutor** is a free project.\nOur goal isn't to copy, but to **understand**. The AI acts like a technical partner.", "support": "Donate", "title": "Groovebox Tutor", "subtitle": "Your technical partner. Decode sound. Master your gear.", "placeholder": "Ask a question...", "onboarding": "👋 **Goal: Autonomy**\n1. Upload your instrument's **Manual**.\n2. Provide a **Sound** that inspires you.\n3. Your partner analyzes the texture and teaches you **the technical steps**.", "legal": "Educational tool. Inspiration is legal, plagiarism is not.", "sugg_1": "Analyze sound", "sugg_2": "Rhythm", "sugg_3": "Feature", "style_label": "Tutor Style", "tones": ["🤙 Cool Mentor", "👔 Technical Expert", "⚡ Direct"], "formats": ["📝 Full Lesson", "✅ Checklist", "💬 Interactive"], "manual_loaded": "✅ Manual loaded", "active_track": "Track:"}
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

# --- 5. INTERFACE ---

# --- SIDEBAR ---
with st.sidebar:
    lang = st.selectbox("Langue / Language", list(TR.keys()), label_visibility="collapsed")
    T = TR.get(lang, TR["Français 🇫🇷"])
    
    # 1. SETUP
    st.markdown(f"### {T['settings']}")
    api_key = st.text_input(T["api_label"], type="password", placeholder="AIzaSy...")
    with st.expander(T["api_help"]):
        st.caption(T["api_desc"])
        st.markdown("[Google AI Studio](https://aistudio.google.com/) (Free)")

    st.markdown("---")
    
    # 2. MACHINE (MANUEL)
    st.markdown(f"### {T['doc_section']}")
    
    # HELPER COMPLET (Tes 7 liens sont là)
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
    
    uploaded_pdf = st.file_uploader(T["manual_upload"], type=["pdf"], label_visibility="collapsed")
    if uploaded_pdf:
        st.success(T["manual_loaded"])

    st.markdown("---")
    
    # 3. OPTIONS & MÉMOIRE (Masqué)
    with st.expander(T["memory_title"]):
        st.caption(T["style_label"])
        style_tone = st.selectbox("Tone", T["tones"], index=0, label_visibility="collapsed")
        style_format = st.radio("Format", T["formats"], index=0, label_visibility="collapsed")
        st.divider()
        uploaded_memory = st.file_uploader(T["memory_load"], type=["txt"], key="mem_up", label_visibility="collapsed")
        if uploaded_memory:
            st.session_state.memory_content = uploaded_memory.getvalue().decode("utf-8")
            st.success("OK")
    
    st.markdown("---")
    
    # FOOTER
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(T["reset"], use_container_width=True):
            st.session_state.clear()
            st.rerun()
    with col_b:
        if "chat_history" in st.session_state and st.session_state.chat_history:
            history_txt = format_history(st.session_state.chat_history)
            st.download_button("💾", history_txt, "session.txt", "text/plain", use_container_width=True, help=T["memory_save"])

    with st.expander(T["about"]):
        st.markdown(T["about_text"])
        st.markdown(f"[{T['support']}](https://www.buymeacoffee.com/)")

# --- MAIN AREA ---
st.title(T["title"])
st.markdown(f"<h3 style='margin-top: -20px; margin-bottom: 40px; color: #808080;'>{T['subtitle']}</h3>", unsafe_allow_html=True)

# Onboarding Pédagogique
if not api_key:
    st.info(T["onboarding"])

# ZONE AUDIO
with st.container(border=True):
    st.subheader(T["audio_title"])
    st.caption(T["audio_subtitle"])
    
    uploaded_audio = st.file_uploader(T["audio_label"], type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    
    if not uploaded_audio:
        st.caption(T["legal"])
    
    if uploaded_audio:
        if "current_audio_name" not in st.session_state or st.session_state.current_audio_name != uploaded_audio.name:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                if "suggested_theme" in st.session_state: del st.session_state.suggested_theme
                st.rerun()

    if "current_audio_path" in st.session_state:
        st.success(f"{T['active_track']} **{st.session_state.get('current_audio_name', 'Inconnu')}**")
        st.audio(st.session_state.current_audio_path)

# --- LOGIC ---
if api_key:
    genai.configure(api_key=api_key)
    
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.status("Lecture du manuel...", expanded=False) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_pdf_to_gemini(p)
            if r: 
                st.session_state.pdf_ref = r
                status.update(label=T["manual_loaded"], state="complete")

    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    prompt = None
    if not st.session_state.chat_history:
        col1, col2, col3 = st.columns(3)
        if col1.button(T["sugg_1"], type="secondary", use_container_width=True): prompt = T["sugg_1"]
        elif col2.button(T["sugg_2"], type="secondary", use_container_width=True): prompt = T["sugg_2"]
        elif col3.button(T["sugg_3"], type="secondary", use_container_width=True): prompt = T["sugg_3"]

    user_input = st.chat_input(T["placeholder"])
    if user_input: prompt = user_input

    if prompt:
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        try: tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except: tools = None
        
        memory_context = ""
        if "memory_content" in st.session_state:
            memory_context = f"CONTEXTE MEMOIRE:\n{st.session_state.memory_content}\n"

        sys_prompt = f"""
        Tu es un expert musical pédagogue (Binôme technique).
        Langue: {lang}. Style: {style_tone}. Format: {style_format}.
        {memory_context}
        MISSION: Analyse l'audio, utilise le manuel PDF, explique la synthèse sonore.
        BUT: Rendre l'utilisateur autonome. Ne pas juste donner la solution, expliquer le pourquoi.
        """
        
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=sys_prompt, tools=tools)
        
        req = [prompt]
        if "pdf_ref" in st.session_state: req.append(st.session_state.pdf_ref)
        if "current_audio_path" in st.session_state:
            audio_path = st.session_state.current_audio_path
            mime = get_mime_type(audio_path)
            audio_data = pathlib.Path(audio_path).read_bytes()
            req.append({"mime_type": mime, "data": audio_data})
            req.append("Analyse l'audio.")

        with st.chat_message("assistant"):
            try:
                resp = model.generate_content(req)
                text_resp = resp.text
                
                match = re.search(r"\|\|GENRE:(.*?)\|\|", text_resp)
                if match:
                    detected_genre = match.group(1).strip()
                    text_resp = text_resp.replace(match.group(0), "")
                    if "Techno" in detected_genre: st.session_state.suggested_theme = "Techno 🤖"
                    elif "House" in detected_genre: st.session_state.suggested_theme = "House 🏠"
                    elif "Lo-Fi" in detected_genre: st.session_state.suggested_theme = "Lo-Fi ☕"
                    elif "Ambient" in detected_genre: st.session_state.suggested_theme = "Ambient 🌌"

                st.markdown(text_resp)
                st.session_state.chat_history.append({"role": "assistant", "content": text_resp})
                if match: st.rerun()
            except Exception as e:
                st.error(f"Erreur IA : {e}")

    if "suggested_theme" in st.session_state and st.session_state.suggested_theme != st.session_state.current_theme:
        with st.container():
            col_msg, col_btn = st.columns([3, 1])
            col_msg.info(f"{T['theme_detected']} **{st.session_state.suggested_theme}**")
            if col_btn.button(T['apply_theme'], use_container_width=True):
                st.session_state.current_theme = st.session_state.suggested_theme
                del st.session_state.suggested_theme
                st.rerun()

else:
    # Warning sidebar si pas de clé
    st.sidebar.warning("🔑 Clé API requise / API Key needed")