import streamlit as st
import google.generativeai as genai
import os
import tempfile
import time
import pathlib
import re
from datetime import datetime

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. THEME ENGINE ---
THEMES = {
    "Default": {"primary": "#238636", "border": "#30363d", "glow": "none", "bg_gradient": "linear-gradient(180deg, #0d1117 0%, #161b22 100%)"},
    "Techno 🤖": {"primary": "#03dac6", "border": "#03dac6", "glow": "0 0 10px rgba(3, 218, 198, 0.4)", "bg_gradient": "linear-gradient(180deg, #001220 0%, #002b36 100%)"},
    "House 🏠": {"primary": "#ff6d00", "border": "#aa00ff", "glow": "0 0 10px rgba(255, 109, 0, 0.4)", "bg_gradient": "linear-gradient(180deg, #1a0526 0%, #2d0c38 100%)"},
    "Lo-Fi ☕": {"primary": "#d4a373", "border": "#bc6c25", "glow": "none", "bg_gradient": "linear-gradient(180deg, #282624 0%, #3e3a36 100%)"},
    "Ambient 🌌": {"primary": "#818cf8", "border": "#a5b4fc", "glow": "0 0 15px rgba(129, 140, 248, 0.3)", "bg_gradient": "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)"}
}

if "current_theme" not in st.session_state: st.session_state.current_theme = "Default"

def apply_theme(theme_name):
    t = THEMES[theme_name]
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono&display=swap');
        html, body, [class*="css"] {{font-family: 'Inter', sans-serif;}}
        .stApp {{background: {t['bg_gradient']};}}
        div[data-testid="stHorizontalBlock"] > div:first-child button {{
            background-color: {t['primary']} !important; color: {'black' if theme_name == 'Techno 🤖' else 'white'} !important;
            border: 1px solid {t['border']}; box-shadow: {t['glow']}; transition: all 0.3s ease;
        }}
        button[kind="secondary"] {{background-color: rgba(255,255,255,0.05); color: {t['primary']}; border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;}}
        button[kind="secondary"]:hover {{border-color: {t['primary']}; box-shadow: {t['glow']};}}
        .stTextInput > div > div > input {{background-color: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: white;}}
        .stTextInput > div > div > input:focus {{border-color: {t['primary']}; box-shadow: {t['glow']};}}
        div[data-testid="stFileUploader"] {{border: 1px dashed {t['primary']}; background-color: rgba(0,0,0,0.2); border-radius: 10px;}}
        #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
        .block-container {{padding-top: 2rem; padding-bottom: 2rem;}}
        [data-testid="stSidebar"] img {{border-radius: 20px !important; box-shadow: 0 0 20px rgba(0,0,0,0.5); margin-bottom: 20px; display: block; margin-left: auto; margin-right: auto;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

apply_theme(st.session_state.current_theme)

# --- 3. DICTIONNAIRE MULTILINGUE (Mise à jour avec Memory) ---
TR = {
    "Français 🇫🇷": {
        "settings": "Réglages",
        "api_help": "ℹ️ Comment avoir une clé gratuite ?",
        "doc_label": "📂 **Documentation (Manuel)**",
        "style_label": "🧠 Style du Prof",
        "memory_label": "💾 Mémoire / Session",
        "memory_upload": "Recharger une session précédente",
        "memory_download": "Télécharger l'historique",
        "reset": "🗑️ Reset",
        "support": "❤️ Soutenir",
        "buy_coffee": "☕ Offrir un café",
        "title": "Groovebox Tutor AI",
        "caption": "Décrypte le son. Maîtrise ta machine. Crée ton propre grain.",
        "audio_title": "🎧 Source Audio",
        "audio_desc": "Importe un fichier audio (MP3, WAV, M4A) pour l'analyser.",
        "drop_label": "Glisse ton fichier ici",
        "active_track": "🎵 Piste active :",
        "manual_loaded": "Manuel chargé !",
        "memory_loaded": "Mémoire rechargée ! L'IA se souvient.",
        "input_placeholder": "Pose ta question ici...",
        "tones": ["🤙 Cool & Pédagogue", "👔 Expert Technique", "⚡ Bref & Direct"],
        "formats": ["📝 Tuto Complet", "✅ Checklist (Pas à pas)", "💬 Interactif (1 étape à la fois)"],
        "sugg_combo": "🔥 Décrypte ce son et donne la recette",
        "sugg_audio": "🥁 Analyse le groove",
        "sugg_pdf": "🎛️ Explique-moi une fonction cachée",
        "sugg_web": "🔍 Trouve une astuce Sound Design",
        "theme_detected": "🎨 Ambiance détectée :",
        "apply_theme": "Appliquer le thème",
        "back_default": "🔙 Retour au défaut"
    },
    "English 🇬🇧": {
        "settings": "Settings",
        "api_help": "ℹ️ How to get a free key?",
        "doc_label": "📂 **Documentation (Manual)**",
        "style_label": "🧠 Tutor Style",
        "memory_label": "💾 Memory / Session",
        "memory_upload": "Load previous session",
        "memory_download": "Download history",
        "reset": "🗑️ Reset",
        "support": "❤️ Support",
        "buy_coffee": "☕ Buy a coffee",
        "title": "Groovebox Tutor AI",
        "caption": "Decode the sound. Master your machine. Craft your tone.",
        "audio_title": "🎧 Audio Source",
        "audio_desc": "Upload an audio file (MP3, WAV, M4A) to analyze.",
        "drop_label": "Drop your file here",
        "active_track": "🎵 Active track:",
        "manual_loaded": "Manual loaded!",
        "memory_loaded": "Memory loaded! AI remembers.",
        "input_placeholder": "Ask your question here...",
        "tones": ["🤙 Cool & Pedagogical", "👔 Technical Expert", "⚡ Short & Direct"],
        "formats": ["📝 Full Tutorial", "✅ Checklist (Step-by-step)", "💬 Interactive (One step at a time)"],
        "sugg_combo": "🔥 Decode sound + Give recipe",
        "sugg_audio": "🥁 Analyze the groove",
        "sugg_pdf": "🎛️ Explain a hidden feature",
        "sugg_web": "🔍 Find a Sound Design tip",
        "theme_detected": "🎨 Vibe detected:",
        "apply_theme": "Apply Theme",
        "back_default": "🔙 Back to Default"
    }
}

# --- FONCTIONS UTILES ---
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

def format_history_for_download(history):
    """Convertit l'historique de chat en texte lisible"""
    text = f"SESSION LOG - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    text += "=========================================\n\n"
    for msg in history:
        role = "USER" if msg['role'] == "user" else "AI"
        text += f"[{role}]:\n{msg['content']}\n\n"
        text += "-----------------------------------------\n"
    return text

# --- SIDEBAR ---
with st.sidebar:
    lang = st.selectbox("Language / Langue 🌍", list(TR.keys()), index=0)
    T = TR.get(lang, TR["Français 🇫🇷"]) # Fallback français si langue manquante
    
    st.image("logo.png", width=120) 
    
    st.title(T["settings"])
    api_key = st.text_input("API Key", type="password")
    with st.expander(T["api_help"]):
        st.markdown("1. [Google AI Studio](https://aistudio.google.com/).\n2. Get API key.\n3. Paste here.")
    
    st.markdown("---")
    
    # 1. PERSONNALISATION
    st.markdown(f"### {T['style_label']}")
    style_tone = st.selectbox("Tone", T["tones"], index=0, label_visibility="collapsed")
    style_format = st.radio("Format", T["formats"], index=0, label_visibility="collapsed")

    # 2. MÉMOIRE (NEW!)
    st.markdown("---")
    st.markdown(f"### {T['memory_label']}")
    
    # Upload (Charger un passif)
    uploaded_memory = st.file_uploader(T["memory_upload"], type=["txt"], key="mem_up")
    if uploaded_memory:
        st.session_state.memory_content = uploaded_memory.getvalue().decode("utf-8")
        st.success(T["memory_loaded"])
    
    # Download (Sauvegarder l'actif)
    if "chat_history" in st.session_state and st.session_state.chat_history:
        history_txt = format_history_for_download(st.session_state.chat_history)
        st.download_button(
            label=f"📥 {T['memory_download']}",
            data=history_txt,
            file_name=f"groovebox_session_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    # 3. THÈME
    st.markdown("---")
    if st.session_state.current_theme != "Default":
        st.markdown(f"🎨 **Thème : {st.session_state.current_theme}**")
        if st.button(T["back_default"], use_container_width=True):
            st.session_state.current_theme = "Default"
            st.rerun()

    # 4. DOCUMENTATION
    st.markdown("---")
    st.info(T["doc_label"])
    uploaded_pdf = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
    
    st.markdown("---")
    col_reset, col_don = st.columns(2)
    with col_reset:
        if st.button(T["reset"], type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
    st.markdown(f"### {T['support']}")
    st.link_button(T["buy_coffee"], "https://www.buymeacoffee.com/", use_container_width=True)

# --- MAIN PAGE ---
st.title(f"🎹 {T['title']}")
st.caption(T["caption"])

# --- AUDIO ZONE ---
with st.container(border=True):
    st.subheader(T["audio_title"])
    st.markdown(T["audio_desc"])
    
    uploaded_audio = st.file_uploader(T["drop_label"], type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    
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
        with st.spinner("Loading PDF..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_pdf_to_gemini(p)
            if r: st.session_state.pdf_ref = r; st.toast(T["manual_loaded"], icon="📘")

    # --- CHAT ---
    st.divider()
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # --- SUGGESTIONS ---
    suggestions = []
    has_audio = "current_audio_path" in st.session_state
    has_pdf = "pdf_ref" in st.session_state

    if has_audio and has_pdf: suggestions.append(T["sugg_combo"])
    if has_audio: suggestions.append(T["sugg_audio"])
    if has_pdf: suggestions.append(T["sugg_pdf"])
    if not suggestions: suggestions.append(T["sugg_web"])

    if suggestions:
        st.markdown(f"<small style='color: #8b949e; margin-bottom: 5px;'>💡 Ideas:</small>", unsafe_allow_html=True)
        cols = st.columns(min(len(suggestions), 3)) 
        choice = None
        for i, col in enumerate(cols):
            if i < 3:
                if col.button(suggestions[i], key=f"sugg_{i}", type="secondary", use_container_width=True):
                    choice = suggestions[i]

    # --- INPUT ---
    prompt = st.chat_input(T["input_placeholder"])
    if choice: prompt = choice
    
    if prompt:
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        try: tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except: tools = None
        
        # --- PROMPT SYSTÈME DYNAMIQUE + MÉMOIRE ---
        memory_context = ""
        if "memory_content" in st.session_state:
            memory_context = f"""
            [MÉMOIRE / CONTEXTE PRÉCÉDENT]
            L'utilisateur a chargé un historique de session précédent. Utilise-le pour comprendre son style et ce qu'il a déjà fait :
            {st.session_state.memory_content}
            [FIN MÉMOIRE]
            """

        sys_prompt = f"""
        Tu es un expert musical. Langue de réponse : {lang}.
        Style: {style_tone}. Format: {style_format}.
        
        {memory_context}
        
        MISSION SECONDAIRE (Genre Detection):
        Si audio fourni, detecte genre parmi [Techno, House, Lo-Fi, Ambient].
        Si détecté, écris à la fin : ||GENRE:Techno||.
        
        MISSION PRINCIPALE :
        Analyse l'audio et aide l'utilisateur avec le manuel.
        """
        
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=sys_prompt, tools=tools)
        
        req = [prompt]
        if "pdf_ref" in st.session_state: req.append(st.session_state.pdf_ref)
        if "current_audio_path" in st.session_state:
            audio_path = st.session_state.current_audio_path
            mime = get_mime_type(audio_path)
            audio_data = pathlib.Path(audio_path).read_bytes()
            req.append({"mime_type": mime, "data": audio_data})
            req.append("⚠️ Analyse l'audio.")

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    resp = model.generate_content(req)
                    text_resp = resp.text
                    
                    # Detection Theme
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
                    st.error(f"Error: {e}")

    if "suggested_theme" in st.session_state and st.session_state.suggested_theme != st.session_state.current_theme:
        with st.container():
            col_msg, col_btn = st.columns([3, 1])
            col_msg.info(f"{T['theme_detected']} **{st.session_state.suggested_theme}**")
            if col_btn.button(T['apply_theme'], use_container_width=True):
                st.session_state.current_theme = st.session_state.suggested_theme
                del st.session_state.suggested_theme
                st.rerun()

else:
    st.warning("👈 Please enter your API Key to start.")