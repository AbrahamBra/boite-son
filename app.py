import streamlit as st
import google.generativeai as genai
import os
import tempfile
import time
import pathlib
import re

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="logo.png", # <--- Mets le nom de ton fichier ici
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SYSTÈME DE THÈMES (THEME ENGINE) ---
# Définition des palettes de couleurs "Pro"
THEMES = {
    "Default": {
        "primary": "#238636", # Vert GitHub
        "border": "#30363d",
        "glow": "none",
        "bg_gradient": "linear-gradient(180deg, #0d1117 0%, #161b22 100%)"
    },
    "Techno 🤖": {
        "primary": "#03dac6", # Cyan Néon
        "border": "#03dac6",
        "glow": "0 0 10px rgba(3, 218, 198, 0.4)",
        "bg_gradient": "linear-gradient(180deg, #001220 0%, #002b36 100%)" # Bleu nuit profond
    },
    "House 🏠": {
        "primary": "#ff6d00", # Orange chaud
        "border": "#aa00ff", # Violet
        "glow": "0 0 10px rgba(255, 109, 0, 0.4)",
        "bg_gradient": "linear-gradient(180deg, #1a0526 0%, #2d0c38 100%)" # Violet club
    },
    "Lo-Fi ☕": {
        "primary": "#d4a373", # Café crème
        "border": "#bc6c25",
        "glow": "none",
        "bg_gradient": "linear-gradient(180deg, #282624 0%, #3e3a36 100%)" # Grain papier
    },
    "Ambient 🌌": {
        "primary": "#818cf8", # Indigo doux
        "border": "#a5b4fc",
        "glow": "0 0 15px rgba(129, 140, 248, 0.3)",
        "bg_gradient": "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)" # Espace calme
    }
}

# Gestion de l'état du thème
if "current_theme" not in st.session_state:
    st.session_state.current_theme = "Default"

# Fonction d'injection CSS dynamique
def apply_theme(theme_name):
    t = THEMES[theme_name]
    
    # CSS Pro & Dynamique
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}
        
        /* Fond global subtil */
        .stApp {{
            background: {t['bg_gradient']};
        }}

        /* Boutons Principaux */
        div[data-testid="stHorizontalBlock"] > div:first-child button {{
            background-color: {t['primary']} !important;
            color: {'black' if theme_name == 'Techno 🤖' else 'white'} !important;
            border: 1px solid {t['border']};
            box-shadow: {t['glow']};
            transition: all 0.3s ease;
        }}
        
        /* Boutons Secondaires (Suggestions) */
        button[kind="secondary"] {{
            background-color: rgba(255,255,255,0.05);
            color: {t['primary']};
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
        }}
        button[kind="secondary"]:hover {{
            border-color: {t['primary']};
            box-shadow: {t['glow']};
        }}
        
        /* Input Fields */
        .stTextInput > div > div > input {{
            background-color: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            color: white;
        }}
        .stTextInput > div > div > input:focus {{
            border-color: {t['primary']};
            box-shadow: {t['glow']};
        }}

        /* Upload Box */
        div[data-testid="stFileUploader"] {{
            border: 1px dashed {t['primary']};
            background-color: rgba(0,0,0,0.2);
            border-radius: 10px;
        }}
        
        /* Masquage Streamlit */
        #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
        .block-container {{padding-top: 2rem; padding-bottom: 2rem;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Application immédiate du thème actif
apply_theme(st.session_state.current_theme)

# --- 3. DICTIONNAIRE DE LANGUES ---
TR = {
    "Français 🇫🇷": {
        "settings": "Réglages",
        "api_help": "ℹ️ Comment avoir une clé gratuite ?",
        "doc_label": "📂 **Documentation (Manuel)**",
        "style_label": "🧠 Style du Prof",
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
    },
    # Tu peux ajouter d'autres langues ici (ES, DE...)
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

# --- SIDEBAR ---
with st.sidebar:
    # 1. Langue
    lang = st.selectbox("Language / Langue 🌍", list(TR.keys()), index=0)
    T = TR[lang]
    
    # 2. Settings de base
    st.image("logo.png", width=80) 
    st.title(T["settings"])
    api_key = st.text_input("API Key", type="password")
    with st.expander(T["api_help"]):
        st.markdown("1. [Google AI Studio](https://aistudio.google.com/).\n2. Get API key.\n3. Paste here.")
    
    st.markdown("---")
    
    # 3. Personnalisation
    st.markdown(f"### {T['style_label']}")
    style_tone = st.selectbox("Tone", T["tones"], index=0, label_visibility="collapsed")
    style_format = st.radio("Format", T["formats"], index=0, label_visibility="collapsed")

    # 4. Gestion du Thème (Bouton Reset)
    st.markdown("---")
    if st.session_state.current_theme != "Default":
        st.markdown(f"🎨 **Thème : {st.session_state.current_theme}**")
        if st.button(T["back_default"], use_container_width=True):
            st.session_state.current_theme = "Default"
            st.rerun()

    # 5. Doc & Reset
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
col1, col2 = st.columns([5, 1])
with col1:
    st.title(T["title"])
    st.caption(T["caption"])

# --- AUDIO ZONE ---
with st.container(border=True):
    st.subheader(T["audio_title"])
    st.markdown(T["audio_desc"])
    
    uploaded_audio = st.file_uploader(T["drop_label"], type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    
     # --- AJOUT DU DISCLAIMER LEGAL ---
    if not uploaded_audio:
        st.caption("⚠️ *Usage strictement personnel et pédagogique. Respectez le droit d'auteur.*")
    # ---------------------------------
    
    if uploaded_audio:
        if "current_audio_name" not in st.session_state or st.session_state.current_audio_name != uploaded_audio.name:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                # Reset des suggestions de thème
                if "suggested_theme" in st.session_state: del st.session_state.suggested_theme
                st.rerun()

    if "current_audio_path" in st.session_state:
        st.success(f"{T['active_track']} **{st.session_state.get('current_audio_name', 'Inconnu')}**")
        st.audio(st.session_state.current_audio_path)

# --- LOGIC ---
if api_key:
    genai.configure(api_key=api_key)
    
    # PDF Handler
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.spinner("Loading PDF..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_pdf_to_gemini(p)
            if r: st.session_state.pdf_ref = r; st.toast(T["manual_loaded"], icon="📘")

    # --- CHAT & THEME DETECTION ---
    st.divider()
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # --- INTELLIGENT SUGGESTIONS ---
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
        
        # --- PROMPT AVANCÉ (AVEC DÉTECTION DE GENRE) ---
        sys_prompt = f"""
        Tu es un expert musical. Langue de réponse : {lang}.
        Style: {style_tone}. Format: {style_format}.
        
        MISSION SECONDAIRE (Analyse de Style) :
        Si un fichier audio est fourni, essaie de définir son genre musical principal en UN SEUL MOT parmi cette liste : [Techno, House, Lo-Fi, Ambient].
        Si tu détectes un de ces genres, écris-le de façon cachée à la toute fin de ta réponse comme ceci : ||GENRE:Techno||.
        
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
                    
                    # Détection du "Vibe Tag" caché
                    detected_genre = None
                    match = re.search(r"\|\|GENRE:(.*?)\|\|", text_resp)
                    if match:
                        detected_genre = match.group(1).strip()
                        # On nettoie la réponse pour ne pas afficher le tag
                        text_resp = text_resp.replace(match.group(0), "")
                        
                        # Mapping vers nos thèmes
                        if "Techno" in detected_genre: st.session_state.suggested_theme = "Techno 🤖"
                        elif "House" in detected_genre: st.session_state.suggested_theme = "House 🏠"
                        elif "Lo-Fi" in detected_genre: st.session_state.suggested_theme = "Lo-Fi ☕"
                        elif "Ambient" in detected_genre: st.session_state.suggested_theme = "Ambient 🌌"

                    st.markdown(text_resp)
                    st.session_state.chat_history.append({"role": "assistant", "content": text_resp})
                    
                    # Si un thème est suggéré, on recharge pour afficher le bouton de switch
                    if detected_genre:
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- NOTIFICATION DE CHANGEMENT DE THÈME ---
    # S'affiche juste après la réponse si un genre est détecté
    if "suggested_theme" in st.session_state and st.session_state.suggested_theme != st.session_state.current_theme:
        with st.container():
            col_msg, col_btn = st.columns([3, 1])
            col_msg.info(f"{T['theme_detected']} **{st.session_state.suggested_theme}**")
            if col_btn.button(T['apply_theme'], use_container_width=True):
                st.session_state.current_theme = st.session_state.suggested_theme
                del st.session_state.suggested_theme
                st.rerun()

else:
    # Si pas de clé
    st.warning("👈 Please enter your API Key to start.")