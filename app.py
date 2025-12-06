import streamlit as st
import google.generativeai as genai
import os
import tempfile
import time
from datetime import datetime

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "PREMIUM STUDIO" ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #E0E0E0;
    }
    
    .stApp {
        background-color: #0E1117;
    }
    [data-testid="stSidebar"] {
        background-color: #0E1117;
        border-right: 1px solid #1F1F1F;
    }

    h1 { font-weight: 600; letter-spacing: -1px; color: #FFFFFF; }
    h2, h3 { font-weight: 400; color: #A0A0A0; }

    .stTextInput > div > div > input {
        background-color: #161920;
        border: 1px solid #303030;
        color: white;
        border-radius: 8px;
        padding: 10px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4A4A4A;
        box-shadow: none;
    }

    .stButton > button {
        background-color: #161920;
        color: white;
        border: 1px solid #303030;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #20242C;
        border-color: #FFFFFF;
    }
    
    div[data-testid="stHorizontalBlock"] > div:first-child button {
        background-color: #FFFFFF;
        color: #000000;
        border: none;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child button:hover {
        background-color: #E0E0E0;
    }

    div[data-testid="stFileUploader"] {
        background-color: #12141A;
        border: 1px dashed #303030;
        border-radius: 12px;
        padding: 30px;
        transition: border 0.3s;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #606060;
    }
    
    button[kind="secondary"] {
        background-color: transparent;
        border: 1px solid #303030;
        border-radius: 20px;
        color: #A0A0A0;
        font-size: 13px;
    }
    button[kind="secondary"]:hover {
        border-color: #FFFFFF;
        color: #FFFFFF;
        background-color: transparent;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 3rem; padding-bottom: 5rem;}
    
    .stTextInput label { font-size: 12px; color: #606060; }
</style>
""", unsafe_allow_html=True)

# --- 3. DICTIONNAIRE TRADUCTION COMPLET ---
TR = {
    "Français 🇫🇷": {
        "settings": "Paramètres",
        "api_label": "Clé API Google",
        "doc_section": "DOCUMENTATION",
        "doc_help": "Trouver mon manuel officiel",
        "manual_upload": "Fichier PDF (Manuel)",
        "audio_section": "STUDIO",
        "audio_label": "Fichier Audio (Source)",
        "memory_section": "SESSION",
        "memory_load": "Charger historique",
        "memory_save": "Sauvegarder",
        "reset": "Nouvelle Session",
        "about": "À propos",
        "title": "Groovebox Tutor",
        "subtitle": "Assistant technique piloté par IA. Analyse sonore et documentation unifiée.",
        "placeholder": "Posez une question technique...",
        "step_1": "1. Entrez votre Clé API (Menu gauche)",
        "step_2": "2. Chargez votre Manuel PDF",
        "step_3": "3. Glissez un son ci-dessous",
        "legal": "Outil d'analyse pédagogique.",
        "sugg_1": "Analyse ce son",
        "sugg_2": "Structure rythmique",
        "sugg_3": "Fonction cachée"
    },
    "English 🇬🇧": {
        "settings": "Settings",
        "api_label": "Google API Key",
        "doc_section": "DOCUMENTATION",
        "doc_help": "Find official manual",
        "manual_upload": "PDF File (Manual)",
        "audio_section": "STUDIO",
        "audio_label": "Audio File (Source)",
        "memory_section": "SESSION",
        "memory_load": "Load history",
        "memory_save": "Save",
        "reset": "New Session",
        "about": "About",
        "title": "Groovebox Tutor",
        "subtitle": "AI-powered technical assistant. Sound analysis and documentation unified.",
        "placeholder": "Ask a technical question...",
        "step_1": "1. Enter API Key (Left Menu)",
        "step_2": "2. Upload PDF Manual",
        "step_3": "3. Drop audio below",
        "legal": "Educational analysis tool.",
        "sugg_1": "Analyze this sound",
        "sugg_2": "Rhythmic structure",
        "sugg_3": "Hidden feature"
    },
    "Español 🇪🇸": {
        "settings": "Configuración",
        "api_label": "Clave API Google",
        "doc_section": "DOCUMENTACIÓN",
        "doc_help": "Encontrar manual oficial",
        "manual_upload": "Archivo PDF (Manual)",
        "audio_section": "ESTUDIO",
        "audio_label": "Archivo de Audio",
        "memory_section": "SESIÓN",
        "memory_load": "Cargar historial",
        "memory_save": "Guardar",
        "reset": "Nueva Sesión",
        "about": "Acerca de",
        "title": "Groovebox Tutor",
        "subtitle": "Asistente técnico con IA. Análisis de sonido y documentación unificada.",
        "placeholder": "Haz una pregunta técnica...",
        "step_1": "1. Ingresa Clave API (Menú izq)",
        "step_2": "2. Sube Manual PDF",
        "step_3": "3. Arrastra audio abajo",
        "legal": "Herramienta educativa.",
        "sugg_1": "Analiza este sonido",
        "sugg_2": "Estructura rítmica",
        "sugg_3": "Función oculta"
    },
    "Deutsch 🇩🇪": {
        "settings": "Einstellungen",
        "api_label": "Google API Key",
        "doc_section": "DOKUMENTATION",
        "doc_help": "Offizielles Handbuch finden",
        "manual_upload": "PDF-Datei (Handbuch)",
        "audio_section": "STUDIO",
        "audio_label": "Audiodatei",
        "memory_section": "SITZUNG",
        "memory_load": "Verlauf laden",
        "memory_save": "Speichern",
        "reset": "Neue Sitzung",
        "about": "Über",
        "title": "Groovebox Tutor",
        "subtitle": "KI-gestützter technischer Assistent. Soundanalyse und Dokumentation vereint.",
        "placeholder": "Stelle eine technische Frage...",
        "step_1": "1. API Key eingeben (Links)",
        "step_2": "2. PDF-Handbuch laden",
        "step_3": "3. Audio unten ablegen",
        "legal": "Bildungstool.",
        "sugg_1": "Analysiere diesen Sound",
        "sugg_2": "Rhythmische Struktur",
        "sugg_3": "Versteckte Funktion"
    },
    "Italiano 🇮🇹": {
        "settings": "Impostazioni",
        "api_label": "Chiave API Google",
        "doc_section": "DOCUMENTAZIONE",
        "doc_help": "Trova manuale ufficiale",
        "manual_upload": "File PDF (Manuale)",
        "audio_section": "STUDIO",
        "audio_label": "File Audio",
        "memory_section": "SESSIONE",
        "memory_load": "Carica cronologia",
        "memory_save": "Salva",
        "reset": "Nuova Sessione",
        "about": "Info",
        "title": "Groovebox Tutor",
        "subtitle": "Assistente tecnico AI. Analisi sonora e documentazione unificata.",
        "placeholder": "Fai una domanda tecnica...",
        "step_1": "1. Inserisci API Key (Menu sx)",
        "step_2": "2. Carica Manuale PDF",
        "step_3": "3. Trascina audio sotto",
        "legal": "Strumento educativo.",
        "sugg_1": "Analizza questo suono",
        "sugg_2": "Struttura ritmica",
        "sugg_3": "Funzione nascosta"
    },
    "Português 🇧🇷": {
        "settings": "Configurações",
        "api_label": "Chave API Google",
        "doc_section": "DOCUMENTAÇÃO",
        "doc_help": "Encontrar manual oficial",
        "manual_upload": "Arquivo PDF (Manual)",
        "audio_section": "ESTÚDIO",
        "audio_label": "Arquivo de Áudio",
        "memory_section": "SESSÃO",
        "memory_load": "Carregar histórico",
        "memory_save": "Salvar",
        "reset": "Nova Sessão",
        "about": "Sobre",
        "title": "Groovebox Tutor",
        "subtitle": "Assistente técnico com IA. Análise sonora e documentação unificada.",
        "placeholder": "Faça uma pergunta técnica...",
        "step_1": "1. Insira Chave API (Menu esq)",
        "step_2": "2. Envie Manual PDF",
        "step_3": "3. Arraste áudio abaixo",
        "legal": "Ferramenta educativa.",
        "sugg_1": "Analise este som",
        "sugg_2": "Estrutura rítmica",
        "sugg_3": "Função oculta"
    },
    "日本語 🇯🇵": {
        "settings": "設定",
        "api_label": "Google APIキー",
        "doc_section": "ドキュメント",
        "doc_help": "公式マニュアルを探す",
        "manual_upload": "PDFファイル (マニュアル)",
        "audio_section": "スタジオ",
        "audio_label": "オーディオファイル",
        "memory_section": "セッション",
        "memory_load": "履歴をロード",
        "memory_save": "保存",
        "reset": "新しいセッション",
        "about": "概要",
        "title": "Groovebox Tutor",
        "subtitle": "AI技術アシスタント。音声分析とドキュメントの統合。",
        "placeholder": "技術的な質問をしてください...",
        "step_1": "1. APIキーを入力 (左メニュー)",
        "step_2": "2. PDFマニュアルをロード",
        "step_3": "3. 音声を下にドロップ",
        "legal": "教育用分析ツール。",
        "sugg_1": "この音を分析",
        "sugg_2": "リズム構造",
        "sugg_3": "隠し機能"
    }
}

# --- 4. FONCTIONS UTILES ---
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

# --- 5. INTERFACE UTILISATEUR ---

# --- SIDEBAR ---
with st.sidebar:
    # Choix de la langue
    lang_options = list(TR.keys())
    lang = st.selectbox("Langue / Language", lang_options, label_visibility="collapsed")
    T = TR[lang] # Chargement des textes dans la bonne langue
    
    st.markdown("### " + T["settings"])
    
    # API Key
    api_key = st.text_input(T["api_label"], type="password", placeholder="AIzaSy...")
    if not api_key:
        st.caption("Une clé est requise pour utiliser l'IA.")
        with st.expander("Obtenir une clé / Get Key"):
            st.markdown("[Google AI Studio](https://aistudio.google.com/) (Free)")

    st.markdown("---")
    
    # Documentation
    st.caption(T["doc_section"])
    with st.expander(T["doc_help"]):
        st.markdown("""
        - [Elektron](https://www.elektron.se/en/support-downloads)
        - [Roland](https://www.roland.com/global/support/)
        - [Korg](https://www.korg.com/us/support/)
        - [Akai](https://www.akaipro.com/support)
        """)
    
    uploaded_pdf = st.file_uploader(T["manual_upload"], type=["pdf"], label_visibility="collapsed")
    if uploaded_pdf:
        st.success(f"Actif : {uploaded_pdf.name}")

    st.markdown("---")
    
    # Session / Mémoire
    st.caption(T["memory_section"])
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(T["reset"], use_container_width=True):
            st.session_state.clear()
            st.rerun()
    with col_b:
        # Bouton Download (Visible seulement si historique existe)
        if "chat_history" in st.session_state and st.session_state.chat_history:
            history_txt = format_history(st.session_state.chat_history)
            st.download_button(T["memory_save"], history_txt, "session.txt", "text/plain", use_container_width=True)

    st.markdown("---")
    with st.expander(T["about"]):
        st.caption("Groovebox Tutor is a free Open Source project dedicated to sound synthesis education.")
        st.markdown("[Support / Donate](https://www.buymeacoffee.com/)")

# --- MAIN AREA ---
st.title(T["title"])
st.markdown(f"<h3 style='margin-top: -20px; margin-bottom: 40px; color: #808080;'>{T['subtitle']}</h3>", unsafe_allow_html=True)

# Message d'accueil (Onboarding)
if not api_key:
    st.info(f"{T['step_1']}")
elif not uploaded_pdf:
    st.info(f"{T['step_2']}")
elif "current_audio_path" not in st.session_state:
    st.info(f"{T['step_3']}")

# Zone Audio
with st.container():
    uploaded_audio = st.file_uploader(T["audio_label"], type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    
    if uploaded_audio:
        if "current_audio_name" not in st.session_state or st.session_state.current_audio_name != uploaded_audio.name:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                st.rerun()

    if "current_audio_path" in st.session_state:
        st.audio(st.session_state.current_audio_path)

# --- CHAT ENGINE ---
if api_key:
    genai.configure(api_key=api_key)
    
    # PDF Processing
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.status("Lecture du manuel / Reading manual...", expanded=False) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_pdf_to_gemini(p)
            if r: 
                st.session_state.pdf_ref = r
                status.update(label="Manuel assimilé / Ready", state="complete")

    # Init History
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    # Display History
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Suggestions (Pills)
    prompt = None
    if not st.session_state.chat_history:
        col1, col2, col3 = st.columns(3)
        if col1.button(T["sugg_1"], type="secondary", use_container_width=True): prompt = T["sugg_1"]
        elif col2.button(T["sugg_2"], type="secondary", use_container_width=True): prompt = T["sugg_2"]
        elif col3.button(T["sugg_3"], type="secondary", use_container_width=True): prompt = T["sugg_3"]

    # Input Box
    user_input = st.chat_input(T["placeholder"])
    if user_input: prompt = user_input

    # AI Processing
    if prompt:
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        try: tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except: tools = None
        
        # Le prompt système force l'IA à parler dans la langue choisie par 'lang'
        sys_prompt = f"Tu es un expert musical pédagogue. Réponds impérativement en : {lang}. Sois clair et technique."
        
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
                st.markdown(resp.text)
                st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
            except Exception as e:
                st.error(f"Erreur IA : {e}")