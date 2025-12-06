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
    /* Distinguer la zone audio principale (plus grande si possible via padding mais limité par streamlit) */
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 3rem; padding-bottom: 5rem;}
    
    /* Info Box */
    div[data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.05); border: 1px solid #303030; color: #E0E0E0; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DICTIONNAIRE MULTILINGUE (COMPLET V11 - 7 LANGUES) ---
TR = {
    "Français 🇫🇷": {
        "settings": "1. Configuration",
        "api_label": "Clé API Google",
        "api_help": "Clé gratuite requise",
        "doc_section": "2. Votre Machine",
        "doc_help": "Où trouver le manuel ?",
        "manual_upload": "Déposer le Manuel PDF ici",
        "audio_title": "🎧 Le Son à Analyser",
        "audio_subtitle": "C'est ici que la magie opère. Glissez votre fichier audio.",
        "audio_label": "Fichier Audio",
        "memory_title": "Options Avancées (Mémoire)",
        "memory_load": "Reprendre une session (.txt)",
        "memory_save": "Sauvegarder Session",
        "reset": "Nouvelle Session",
        "about": "Philosophie",
        "about_text": "**Groovebox Tutor** est un outil libre.\nBut : **Comprendre**, pas copier.",
        "support": "Soutenir (Don)",
        "title": "Groovebox Tutor",
        "subtitle": "Votre binôme technique. Décryptez le son. Maîtrisez votre machine.",
        "placeholder": "Posez une question technique sur ce son...",
        "onboarding": "👋 **Bienvenue !**\n\n**Étape 1 (Gauche) :** Entrez votre Clé API et chargez le Manuel PDF.\n**Étape 2 (Ci-dessous) :** Glissez le son que vous voulez reproduire.",
        "legal": "⚠️ Outil pédagogique. Respectez le droit d'auteur.",
        "sugg_1": "Analyse ce son",
        "sugg_2": "Structure rythmique",
        "sugg_3": "Fonction cachée",
        "style_label": "Style du Prof",
        "tones": ["🤙 Mentor Cool", "👔 Expert Technique", "⚡ Direct"],
        "formats": ["📝 Cours Complet", "✅ Checklist", "💬 Interactif"],
        "manual_loaded": "✅ Manuel assimilé",
        "active_track": "Piste active :"
    },
    "English 🇬🇧": {
        "settings": "1. Setup",
        "api_label": "Google API Key",
        "api_help": "Free key required",
        "doc_section": "2. Your Gear",
        "doc_help": "Find manual",
        "manual_upload": "Drop PDF Manual here",
        "audio_title": "🎧 The Sound",
        "audio_subtitle": "Magic happens here. Drop your audio file.",
        "audio_label": "Audio File",
        "memory_title": "Advanced (Memory)",
        "memory_load": "Load Session",
        "memory_save": "Save Session",
        "reset": "New Session",
        "about": "Philosophy",
        "about_text": "Free tool to understand synthesis.",
        "support": "Donate",
        "title": "Groovebox Tutor",
        "subtitle": "Your technical partner. Decode sound. Master your gear.",
        "placeholder": "Ask a technical question...",
        "onboarding": "👋 **Welcome!**\n**Step 1 (Left):** Setup Key & Manual.\n**Step 2 (Below):** Drop your sound.",
        "legal": "Educational tool. Respect copyright.",
        "sugg_1": "Analyze sound",
        "sugg_2": "Rhythm",
        "sugg_3": "Hidden feature",
        "style_label": "Tutor Style",
        "tones": ["🤙 Cool", "👔 Expert", "⚡ Direct"],
        "formats": ["📝 Full Lesson", "✅ Checklist", "💬 Interactive"],
        "manual_loaded": "✅ Manual loaded",
        "active_track": "Track:"
    },
    "Español 🇪🇸": {
        "settings": "1. Configuración",
        "api_label": "Clave API Google",
        "api_help": "Clave gratuita requerida",
        "doc_section": "2. Tu Máquina",
        "doc_help": "¿Dónde encontrar el manual?",
        "manual_upload": "Suelta el Manual PDF aquí",
        "audio_title": "🎧 El Sonido",
        "audio_subtitle": "Aquí ocurre la magia. Arrastra tu archivo de audio.",
        "audio_label": "Archivo de Audio",
        "memory_title": "Opciones Avanzadas (Memoria)",
        "memory_load": "Cargar Sesión",
        "memory_save": "Guardar Sesión",
        "reset": "Nueva Sesión",
        "about": "Filosofía",
        "about_text": "Herramienta libre para entender la síntesis.",
        "support": "Donar",
        "title": "Groovebox Tutor",
        "subtitle": "Tu socio técnico. Decodifica el sonido. Domina tu máquina.",
        "placeholder": "Haz una pregunta técnica...",
        "onboarding": "👋 **¡Bienvenido!**\n**Paso 1 (Izq):** Configura Clave y Manual.\n**Paso 2 (Abajo):** Arrastra tu sonido.",
        "legal": "Herramienta educativa. Respeta el copyright.",
        "sugg_1": "Analiza sonido",
        "sugg_2": "Ritmo",
        "sugg_3": "Función oculta",
        "style_label": "Estilo",
        "tones": ["🤙 Genial", "👔 Experto", "⚡ Directo"],
        "formats": ["📝 Lección", "✅ Checklist", "💬 Interactivo"],
        "manual_loaded": "✅ Manual cargado",
        "active_track": "Pista:"
    },
    "Deutsch 🇩🇪": {
        "settings": "1. Einrichtung",
        "api_label": "Google API Key",
        "api_help": "Kostenloser Key erforderlich",
        "doc_section": "2. Deine Maschine",
        "doc_help": "Handbuch finden?",
        "manual_upload": "PDF-Handbuch hier ablegen",
        "audio_title": "🎧 Der Sound",
        "audio_subtitle": "Hier passiert die Magie. Ziehe deine Datei hierher.",
        "audio_label": "Audiodatei",
        "memory_title": "Erweitert (Speicher)",
        "memory_load": "Sitzung laden",
        "memory_save": "Sitzung speichern",
        "reset": "Neue Sitzung",
        "about": "Philosophie",
        "about_text": "Freies Tool zum Verständnis der Synthese.",
        "support": "Spenden",
        "title": "Groovebox Tutor",
        "subtitle": "Dein technischer Partner. Entschlüssle den Sound.",
        "placeholder": "Stelle eine technische Frage...",
        "onboarding": "👋 **Willkommen!**\n**Schritt 1 (Links):** Key & Handbuch.\n**Schritt 2 (Unten):** Sound ablegen.",
        "legal": "Bildungstool. Urheberrecht beachten.",
        "sugg_1": "Analyse Sound",
        "sugg_2": "Rhythmus",
        "sugg_3": "Funktion",
        "style_label": "Stil",
        "tones": ["🤙 Cool", "👔 Experte", "⚡ Direkt"],
        "formats": ["📝 Lektion", "✅ Checkliste", "💬 Interaktiv"],
        "manual_loaded": "✅ Handbuch geladen",
        "active_track": "Track:"
    },
    "Italiano 🇮🇹": {
        "settings": "1. Configurazione",
        "api_label": "Chiave API Google",
        "api_help": "Chiave gratuita richiesta",
        "doc_section": "2. La tua Macchina",
        "doc_help": "Trova manuale",
        "manual_upload": "Rilascia il Manuale PDF qui",
        "audio_title": "🎧 Il Suono",
        "audio_subtitle": "Qui avviene la magia. Trascina il tuo file audio.",
        "audio_label": "File Audio",
        "memory_title": "Avanzate (Memoria)",
        "memory_load": "Carica Sessione",
        "memory_save": "Salva Sessione",
        "reset": "Nuova Sessione",
        "about": "Filosofia",
        "about_text": "Strumento libero per capire la sintesi.",
        "support": "Dona",
        "title": "Groovebox Tutor",
        "subtitle": "Il tuo partner tecnico. Decodifica il suono.",
        "placeholder": "Fai una domanda tecnica...",
        "onboarding": "👋 **Benvenuto!**\n**Step 1 (Sx):** Chiave & Manuale.\n**Step 2 (Sotto):** Trascina il suono.",
        "legal": "Strumento educativo. Rispetta il copyright.",
        "sugg_1": "Analizza suono",
        "sugg_2": "Ritmo",
        "sugg_3": "Funzione",
        "style_label": "Stile",
        "tones": ["🤙 Cool", "👔 Esperto", "⚡ Diretto"],
        "formats": ["📝 Lezione", "✅ Checklist", "💬 Interattivo"],
        "manual_loaded": "✅ Manuale caricato",
        "active_track": "Traccia:"
    },
    "Português 🇧🇷": {
        "settings": "1. Configuração",
        "api_label": "Chave API Google",
        "api_help": "Chave gratuita necessária",
        "doc_section": "2. Sua Máquina",
        "doc_help": "Encontrar manual",
        "manual_upload": "Solte o Manual PDF aqui",
        "audio_title": "🎧 O Som",
        "audio_subtitle": "A mágica acontece aqui. Arraste seu áudio.",
        "audio_label": "Arquivo de Áudio",
        "memory_title": "Avançado (Memória)",
        "memory_load": "Carregar Sessão",
        "memory_save": "Salvar Sessão",
        "reset": "Nova Sessão",
        "about": "Filosofia",
        "about_text": "Ferramenta livre para entender síntese.",
        "support": "Doar",
        "title": "Groovebox Tutor",
        "subtitle": "Seu parceiro técnico. Decodifique o som.",
        "placeholder": "Faça uma pergunta técnica...",
        "onboarding": "👋 **Bem-vindo!**\n**Passo 1 (Esq):** Chave & Manual.\n**Passo 2 (Abaixo):** Arraste o som.",
        "legal": "Ferramenta educativa. Respeite os direitos.",
        "sugg_1": "Analise som",
        "sugg_2": "Ritmo",
        "sugg_3": "Função",
        "style_label": "Estilo",
        "tones": ["🤙 Legal", "👔 Especialista", "⚡ Direto"],
        "formats": ["📝 Aula", "✅ Checklist", "💬 Interativo"],
        "manual_loaded": "✅ Manual carregado",
        "active_track": "Faixa:"
    },
    "日本語 🇯🇵": {
        "settings": "1. 設定",
        "api_label": "Google APIキー",
        "api_help": "無料キーが必要です",
        "doc_section": "2. あなたのマシン",
        "doc_help": "マニュアルを探す",
        "manual_upload": "PDFマニュアルをここにドロップ",
        "audio_title": "🎧 サウンド",
        "audio_subtitle": "魔法はここで起きます。オーディオファイルをドロップ。",
        "audio_label": "オーディオファイル",
        "memory_title": "詳細設定 (メモリ)",
        "memory_load": "セッション読込",
        "memory_save": "セッション保存",
        "reset": "新規セッション",
        "about": "哲学",
        "about_text": "シンセサイズを理解するための無料ツール。",
        "support": "寄付",
        "title": "Groovebox Tutor",
        "subtitle": "あなたの技術パートナー。音を解読します。",
        "placeholder": "技術的な質問をどうぞ...",
        "onboarding": "👋 **ようこそ！**\n**手順 1 (左):** キーとマニュアルを設定。\n**手順 2 (下):** 音をドロップ。",
        "legal": "教育ツール。著作権を尊重してください。",
        "sugg_1": "分析する",
        "sugg_2": "リズム",
        "sugg_3": "機能",
        "style_label": "スタイル",
        "tones": ["🤙 フレンドリー", "👔 専門的", "⚡ 直接的"],
        "formats": ["📝 レッスン", "✅ チェックリスト", "💬 対話"],
        "manual_loaded": "✅ マニュアル完了",
        "active_track": "トラック:"
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

# --- 5. INTERFACE ---

# --- SIDEBAR (Context & Setup) ---
with st.sidebar:
    # Langue
    lang_options = list(TR.keys())
    lang = st.selectbox("Langue / Language", lang_options, label_visibility="collapsed")
    T = TR.get(lang, TR["Français 🇫🇷"])
    
    # BLOC 1 : SETUP (Clé)
    st.markdown(f"### {T['settings']}")
    api_key = st.text_input(T["api_label"], type="password", placeholder="AIzaSy...")
    with st.expander(T["api_help"]):
        st.markdown("[Google AI Studio](https://aistudio.google.com/) (Free)")

    st.markdown("---")
    
    # BLOC 2 : MACHINE (Le Manuel)
    st.markdown(f"### {T['doc_section']}")
    
    # Helper liens (Compact)
    with st.expander(T["doc_help"]):
        MANUAL_LINKS = {"Elektron": "https://www.elektron.se/en/support-downloads", "Roland": "https://www.roland.com/global/support/", "Korg": "https://www.korg.com/us/support/"}
        brand = st.selectbox("Marque", list(MANUAL_LINKS.keys()), label_visibility="collapsed")
        st.link_button(f"Go to {brand}", MANUAL_LINKS[brand], use_container_width=True)
    
    # L'upload du manuel est ici, bien identifié par le titre "2. Votre Machine"
    uploaded_pdf = st.file_uploader(T["manual_upload"], type=["pdf"], label_visibility="collapsed")
    if uploaded_pdf:
        st.success(T["manual_loaded"])

    st.markdown("---")
    
    # BLOC 3 : OPTIONS & MÉMOIRE (Masqué par défaut pour clarté)
    with st.expander(T["memory_title"]):
        # Style
        st.caption(T["style_label"])
        style_tone = st.selectbox("Tone", T["tones"], index=0, label_visibility="collapsed")
        style_format = st.radio("Format", T["formats"], index=0, label_visibility="collapsed")
        
        st.divider()
        
        # Mémoire Upload
        uploaded_memory = st.file_uploader(T["memory_load"], type=["txt"], key="mem_up", label_visibility="collapsed")
        if uploaded_memory:
            st.session_state.memory_content = uploaded_memory.getvalue().decode("utf-8")
            st.success("OK")
    
    st.markdown("---")
    
    # PIED DE PAGE
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
        st.caption(T["about_text"])
        st.markdown(f"[{T['support']}](https://www.buymeacoffee.com/)")

# --- MAIN AREA (Action) ---
st.title(T["title"])
st.markdown(f"<h3 style='margin-top: -20px; margin-bottom: 40px; color: #808080;'>{T['subtitle']}</h3>", unsafe_allow_html=True)

# Onboarding clair
if not api_key:
    st.info(T["onboarding"])

# ZONE AUDIO (La Star)
with st.container(border=True):
    st.subheader(T["audio_title"])
    st.caption(T["audio_subtitle"])
    
    # C'est la seule grosse zone de drop visible au premier abord
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

# --- CHAT LOGIC ---
if api_key:
    genai.configure(api_key=api_key)
    
    # PDF Processing
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.status("Lecture du manuel...", expanded=False) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_pdf_to_gemini(p)
            if r: 
                st.session_state.pdf_ref = r
                status.update(label=T["manual_loaded"], state="complete")

    # History & Chat Display
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Suggestions
    prompt = None
    if not st.session_state.chat_history:
        col1, col2, col3 = st.columns(3)
        if col1.button(T["sugg_1"], type="secondary", use_container_width=True): prompt = T["sugg_1"]
        elif col2.button(T["sugg_2"], type="secondary", use_container_width=True): prompt = T["sugg_2"]
        elif col3.button(T["sugg_3"], type="secondary", use_container_width=True): prompt = T["sugg_3"]

    # Input
    user_input = st.chat_input(T["placeholder"])
    if user_input: prompt = user_input

    # AI
    if prompt:
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        try: tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except: tools = None
        
        memory_context = ""
        if "memory_content" in st.session_state:
            memory_context = f"CONTEXTE MEMOIRE:\n{st.session_state.memory_content}\n"

        sys_prompt = f"""
        Tu es un expert musical pédagogue.
        Langue: {lang}. Style: {style_tone}. Format: {style_format}.
        {memory_context}
        MISSION: Analyse l'audio, utilise le manuel, explique la synthèse.
        GENRE DETECTION: Si Techno/House/Lo-Fi/Ambient, écrit ||GENRE:Style|| à la fin.
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

    # Theme Switcher Notification
    if "suggested_theme" in st.session_state and st.session_state.suggested_theme != st.session_state.current_theme:
        with st.container():
            col_msg, col_btn = st.columns([3, 1])
            col_msg.info(f"{T['theme_detected']} **{st.session_state.suggested_theme}**")
            if col_btn.button(T['apply_theme'], use_container_width=True):
                st.session_state.current_theme = st.session_state.suggested_theme
                del st.session_state.suggested_theme
                st.rerun()

else:
    # Sidebar warning if no key
    st.sidebar.warning("🔑 Clé API requise")