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

# --- 3. CONTENU RICHE (7 LANGUES + VISION PÉDAGOGIQUE) ---
TR = {
    "Français 🇫🇷": {
        "settings": "Réglages",
        "api_label": "Clé API Google",
        "api_help": "Pourquoi une clé perso ?",
        "api_desc": "Projet open-source. L'usage de votre clé gratuite garantit l'indépendance de l'outil.",
        "doc_section": "DOCUMENTATION",
        "doc_help": "Trouver mon manuel officiel",
        "manual_upload": "Fichier PDF (Manuel)",
        "helper_machine": "Votre machine :",
        "helper_dl": "Télécharger le PDF :",
        "helper_site": "Site Officiel",
        "audio_section": "STUDIO",
        "audio_label": "Fichier Audio (Source)",
        "memory_section": "SESSION",
        "memory_load": "Charger historique (.txt)",
        "memory_save": "Sauvegarder",
        "reset": "Nouvelle Session",
        "about": "Philosophie du projet",
        "about_text": "**Groovebox Tutor** est un outil libre.\nNotre but n'est pas de copier, mais de **comprendre**. L'IA agit comme un binôme technique.",
        "support": "Soutenir (Don)",
        "title": "Groovebox Tutor",
        "subtitle": "Votre binôme technique. Décryptez le son. Maîtrisez votre machine.",
        "placeholder": "Posez une question technique...",
        "onboarding": "👋 **Bienvenue ! Pour commencer :**\n1. **Clé API :** Entrez votre clé Google gratuite dans le menu à gauche.\n2. **Manuel :** Chargez le PDF de votre machine.\n3. **Son :** Glissez un fichier audio ci-dessous pour lancer l'analyse.",
        "legal": "⚠️ Outil pédagogique. L'inspiration est légale, le plagiat ne l'est pas.",
        "sugg_1": "Analyse ce son",
        "sugg_2": "Structure rythmique",
        "sugg_3": "Fonction cachée",
        "style_label": "Approche Pédagogique",
        "tones": ["🤙 Mentor Cool", "👔 Expert Technique", "⚡ Direct"],
        "formats": ["📝 Cours Complet", "✅ Checklist", "💬 Interactif"],
        "manual_loaded": "Manuel assimilé",
        "active_track": "Piste active :"
    },
    "English 🇬🇧": {
        "settings": "Settings",
        "api_label": "Google API Key",
        "api_help": "Why a personal key?",
        "api_desc": "Open-source project. Using your own free key ensures tool independence.",
        "doc_section": "DOCUMENTATION",
        "doc_help": "Find official manual",
        "manual_upload": "PDF File (Manual)",
        "helper_machine": "Your machine:",
        "helper_dl": "Download PDF:",
        "helper_site": "Official Site",
        "audio_section": "STUDIO",
        "audio_label": "Audio File (Source)",
        "memory_section": "SESSION",
        "memory_load": "Load history (.txt)",
        "memory_save": "Save",
        "reset": "New Session",
        "about": "Project Philosophy",
        "about_text": "**Groovebox Tutor** is free software.\nOur goal is not to copy, but to **understand**. The AI acts as a technical partner.",
        "support": "Support (Donate)",
        "title": "Groovebox Tutor",
        "subtitle": "Your technical partner. Decode sound. Master your gear.",
        "placeholder": "Ask a technical question...",
        "onboarding": "👋 **Welcome! To start:**\n1. **API Key:** Enter your free Google Key in the left menu.\n2. **Manual:** Upload your machine's PDF.\n3. **Sound:** Drop an audio file below to start analysis.",
        "legal": "⚠️ Educational tool. Inspiration is legal, plagiarism is not.",
        "sugg_1": "Analyze this sound",
        "sugg_2": "Rhythmic structure",
        "sugg_3": "Hidden feature",
        "style_label": "Pedagogical Approach",
        "tones": ["🤙 Cool Mentor", "👔 Technical Expert", "⚡ Direct"],
        "formats": ["📝 Full Lesson", "✅ Checklist", "💬 Interactive"],
        "manual_loaded": "Manual loaded",
        "active_track": "Active track:"
    },
    "Español 🇪🇸": {
        "settings": "Configuración",
        "api_label": "Clave API Google",
        "api_help": "¿Por qué clave personal?",
        "api_desc": "Proyecto open-source. Usar tu propia clave garantiza la independencia.",
        "doc_section": "DOCUMENTACIÓN",
        "doc_help": "Encontrar manual oficial",
        "manual_upload": "Archivo PDF (Manual)",
        "helper_machine": "Tu máquina:",
        "helper_dl": "Descargar PDF:",
        "helper_site": "Sitio Oficial",
        "audio_section": "ESTUDIO",
        "audio_label": "Archivo de Audio",
        "memory_section": "SESIÓN",
        "memory_load": "Cargar historial",
        "memory_save": "Guardar",
        "reset": "Nueva Sesión",
        "about": "Filosofía",
        "about_text": "**Groovebox Tutor** es software libre.\nNuestro objetivo es **entender**. La IA actúa como un socio técnico.",
        "support": "Apoyar (Donar)",
        "title": "Groovebox Tutor",
        "subtitle": "Tu socio técnico. Decodifica el sonido. Domina tu máquina.",
        "placeholder": "Haz una pregunta técnica...",
        "onboarding": "👋 **¡Bienvenido! Para empezar:**\n1. **Clave API:** Ingresa tu clave gratuita a la izquierda.\n2. **Manual:** Sube el PDF.\n3. **Sonido:** Arrastra un audio abajo.",
        "legal": "⚠️ Herramienta educativa.",
        "sugg_1": "Analiza este sonido",
        "sugg_2": "Estructura rítmica",
        "sugg_3": "Función oculta",
        "style_label": "Enfoque Pedagógico",
        "tones": ["🤙 Mentor Genial", "👔 Experto Técnico", "⚡ Directo"],
        "formats": ["📝 Lección Completa", "✅ Checklist", "💬 Interactivo"],
        "manual_loaded": "Manual cargado",
        "active_track": "Pista activa:"
    },
    "Deutsch 🇩🇪": {
        "settings": "Einstellungen",
        "api_label": "Google API Key",
        "api_help": "Warum eigener Key?",
        "api_desc": "Open-Source-Projekt. Dein eigener Key garantiert Unabhängigkeit.",
        "doc_section": "DOKUMENTATION",
        "doc_help": "Offizielles Handbuch finden",
        "manual_upload": "PDF-Datei (Handbuch)",
        "helper_machine": "Deine Maschine:",
        "helper_dl": "PDF herunterladen:",
        "helper_site": "Offizielle Seite",
        "audio_section": "STUDIO",
        "audio_label": "Audiodatei",
        "memory_section": "SITZUNG",
        "memory_load": "Verlauf laden",
        "memory_save": "Speichern",
        "reset": "Neue Sitzung",
        "about": "Philosophie",
        "about_text": "**Groovebox Tutor** ist freie Software.\nZiel ist **Verstehen**. Die KI ist dein technischer Partner.",
        "support": "Unterstützen",
        "title": "Groovebox Tutor",
        "subtitle": "Dein technischer Partner. Entschlüssle den Sound. Beherrsche deine Maschine.",
        "placeholder": "Stelle eine Frage...",
        "onboarding": "👋 **Willkommen!**\n1. **API Key:** Gib deinen Key links ein.\n2. **Handbuch:** Lade das PDF hoch.\n3. **Sound:** Ziehe eine Datei nach unten.",
        "legal": "⚠️ Bildungstool.",
        "sugg_1": "Analysiere Sound",
        "sugg_2": "Rhythmus",
        "sugg_3": "Versteckte Funktion",
        "style_label": "Pädagogischer Ansatz",
        "tones": ["🤙 Cool", "👔 Experte", "⚡ Direkt"],
        "formats": ["📝 Lektion", "✅ Checkliste", "💬 Interaktiv"],
        "manual_loaded": "Handbuch geladen",
        "active_track": "Aktiver Track:"
    },
    "Italiano 🇮🇹": {
        "settings": "Impostazioni",
        "api_label": "Chiave API Google",
        "api_help": "Perché chiave personale?",
        "api_desc": "Progetto open-source. La tua chiave garantisce indipendenza.",
        "doc_section": "DOCUMENTAZIONE",
        "doc_help": "Trova manuale ufficiale",
        "manual_upload": "File PDF (Manuale)",
        "helper_machine": "La tua macchina:",
        "helper_dl": "Scarica PDF:",
        "helper_site": "Sito Ufficiale",
        "audio_section": "STUDIO",
        "audio_label": "File Audio",
        "memory_section": "SESSIONE",
        "memory_load": "Carica cronologia",
        "memory_save": "Salva",
        "reset": "Nuova Sessione",
        "about": "Filosofia",
        "about_text": "**Groovebox Tutor** è software libero.\nL'obiettivo è **capire**. L'IA è il tuo partner tecnico.",
        "support": "Supporta",
        "title": "Groovebox Tutor",
        "subtitle": "Il tuo partner tecnico. Decodifica il suono. Padroneggia la macchina.",
        "placeholder": "Fai una domanda...",
        "onboarding": "👋 **Benvenuto!**\n1. **API Key:** Inserisci la chiave a sinistra.\n2. **Manuale:** Carica il PDF.\n3. **Suono:** Trascina un file audio qui sotto.",
        "legal": "⚠️ Strumento educativo.",
        "sugg_1": "Analizza suono",
        "sugg_2": "Ritmo",
        "sugg_3": "Funzione nascosta",
        "style_label": "Approccio Pedagogico",
        "tones": ["🤙 Mentor Cool", "👔 Esperto", "⚡ Diretto"],
        "formats": ["📝 Lezione", "✅ Checklist", "💬 Interattivo"],
        "manual_loaded": "Manuale caricato",
        "active_track": "Traccia attiva:"
    },
    "Português 🇧🇷": {
        "settings": "Configurações",
        "api_label": "Chave API Google",
        "api_help": "Por que chave pessoal?",
        "api_desc": "Projeto open-source. Sua chave garante independência.",
        "doc_section": "DOCUMENTAÇÃO",
        "doc_help": "Encontrar manual oficial",
        "manual_upload": "Arquivo PDF (Manual)",
        "helper_machine": "Sua máquina:",
        "helper_dl": "Baixar PDF:",
        "helper_site": "Site Oficial",
        "audio_section": "ESTÚDIO",
        "audio_label": "Arquivo de Áudio",
        "memory_section": "SESSÃO",
        "memory_load": "Carregar histórico",
        "memory_save": "Salvar",
        "reset": "Nova Sessão",
        "about": "Filosofia",
        "about_text": "**Groovebox Tutor** é software livre.\nO objetivo é **entender**. A IA é seu parceiro técnico.",
        "support": "Apoiar",
        "title": "Groovebox Tutor",
        "subtitle": "Seu parceiro técnico. Decodifique o som. Domine sua máquina.",
        "placeholder": "Faça uma pergunta...",
        "onboarding": "👋 **Bem-vindo!**\n1. **Chave API:** Insira sua chave à esquerda.\n2. **Manual:** Envie o PDF.\n3. **Som:** Arraste um arquivo abaixo.",
        "legal": "⚠️ Ferramenta educativa.",
        "sugg_1": "Analise o som",
        "sugg_2": "Ritmo",
        "sugg_3": "Função oculta",
        "style_label": "Abordagem Pedagógica",
        "tones": ["🤙 Mentor Legal", "👔 Especialista", "⚡ Direto"],
        "formats": ["📝 Aula", "✅ Checklist", "💬 Interativo"],
        "manual_loaded": "Manual carregado",
        "active_track": "Faixa ativa:"
    },
    "日本語 🇯🇵": {
        "settings": "設定",
        "api_label": "Google APIキー",
        "api_help": "なぜ個人のキー？",
        "api_desc": "オープンソースプロジェクトです。個人のキーで独立性を保証します。",
        "doc_section": "ドキュメント",
        "doc_help": "公式マニュアルを探す",
        "manual_upload": "PDFファイル (マニュアル)",
        "helper_machine": "機種:",
        "helper_dl": "PDFをダウンロード:",
        "helper_site": "公式サイト",
        "audio_section": "スタジオ",
        "audio_label": "オーディオファイル",
        "memory_section": "セッション",
        "memory_load": "履歴をロード",
        "memory_save": "保存",
        "reset": "新しいセッション",
        "about": "哲学",
        "about_text": "**Groovebox Tutor** はフリーソフトウェアです。\n目的はコピーではなく**理解**です。",
        "support": "支援する",
        "title": "Groovebox Tutor",
        "subtitle": "あなたの技術パートナー。音を解読し、マシンを支配する。",
        "placeholder": "質問してください...",
        "onboarding": "👋 **ようこそ！**\n1. **APIキー:** 左のメニューに入力してください。\n2. **マニュアル:** PDFをロード。\n3. **音:** 下にファイルをドロップ。",
        "legal": "⚠️ 教育用ツール。",
        "sugg_1": "この音を分析",
        "sugg_2": "リズム",
        "sugg_3": "隠し機能",
        "style_label": "教育アプローチ",
        "tones": ["🤙 フレンドリー", "👔 エキスパート", "⚡ 簡潔"],
        "formats": ["📝 レッスン", "✅ 手順", "💬 対話モード"],
        "manual_loaded": "マニュアル完了",
        "active_track": "再生中:"
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