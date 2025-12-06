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
        /* Info Box Styling */
        div[data-testid="stAlert"] {{background-color: rgba(255,255,255,0.05); border: 1px solid {t['primary']}; color: white;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

apply_theme(st.session_state.current_theme)

# --- 3. DICTIONNAIRE MULTILINGUE (VISION PÉDAGOGIQUE & LIBRE) ---
TR = {
    "Français 🇫🇷": {
        "settings": "Réglages",
        "api_label": "Clé API Google",
        "api_help": "ℹ️ Pourquoi une clé perso ?",
        "api_desc": "Ce projet est open-source et gratuit. Pour qu'il le reste, chacun utilise sa propre clé (quota gratuit Google). C'est ce qui garantit votre indépendance.",
        "doc_label": "📂 **Votre Manuel (La source de vérité)**",
        "helper_title": "🔍 Trouver mon manuel officiel",
        "helper_machine": "Votre machine :",
        "helper_dl": "1. Télécharger le PDF :",
        "helper_site": "Site Constructeur",
        "helper_drag": "2. Déposez-le ci-dessous 👇",
        "pdf_drop_label": "Fichier PDF du manuel",
        "style_label": "🧠 Approche Pédagogique",
        "memory_label": "💾 Continuité Pédagogique",
        "memory_upload": "Reprendre une session (.txt)",
        "memory_download": "Sauvegarder mes notes",
        "reset": "🗑️ Nouvelle Session",
        "about_title": "ℹ️ Philosophie du projet",
        "about_text": "**Groovebox Tutor** est un projet libre, né du désir de reconnecter les musiciens avec leurs machines.\n\nNotre but n'est pas de copier, mais de **comprendre**. L'IA agit comme un ingénieur du son assis à côté de vous : elle écoute, elle lit la doc, et elle vous explique *comment* sculpter votre propre son.\n\nL'outil est gratuit. Si vous apprenez des choses grâce à lui, vous pouvez soutenir son développement.",
        "buy_coffee": "☕ Soutenir le projet (Don)",
        "title": "Groovebox Tutor AI",
        "caption": "Votre mentor de studio. Comprenez la synthèse. Maîtrisez votre machine.",
        "how_to": "👋 **Objectif : Autonomie**\n1. Importez le **Manuel** de votre instrument.\n2. Proposez un **Son** qui vous inspire.\n3. Votre assistant analyse la texture et vous enseigne **les étapes techniques** pour recréer ce grain vous-même.",
        "audio_title": "🎧 Matériau Sonore",
        "audio_desc": "Support d'analyse (MP3, WAV, M4A).",
        "drop_label": "Déposez votre fichier audio ici",
        "legal_warning": "⚠️ *Outil d'analyse à but éducatif. L'inspiration est légale, le plagiat ne l'est pas.*",
        "active_track": "🎵 Analyse en cours sur :",
        "unknown_track": "Fichier inconnu",
        "manual_loaded": "Connaissances techniques assimilées !",
        "memory_loaded": "Contexte de l'élève chargé !",
        "input_placeholder": "Posez votre question à votre mentor...",
        "tones": ["🤙 Mentor Encouragent", "👔 Expert Technique", "⚡ Synthétique & Direct"],
        "formats": ["📝 Cours Complet", "✅ Checklist (Actionable)", "💬 Mode Interactif (Pas à pas)"],
        "sugg_combo": "🔥 Analyse ce son et explique-moi la synthèse",
        "sugg_audio": "🥁 Décompose la structure rythmique",
        "sugg_pdf": "🎛️ À quoi sert cette fonction précise ?",
        "sugg_web": "🔍 Je cherche une technique de Sound Design",
        "theme_detected": "🎨 Ambiance détectée :",
        "apply_theme": "Appliquer le thème",
        "back_default": "🔙 Retour au défaut"
    },
    "English 🇬🇧": {
        "settings": "Settings",
        "api_label": "Google API Key",
        "api_help": "ℹ️ Why a personal key?",
        "api_desc": "This is a free, open-source project. To keep it running, everyone uses their own free Google quota key. This ensures your independence and privacy.",
        "doc_label": "📂 **Your Manual (The Truth)**",
        "helper_title": "🔍 Find official manual",
        "helper_machine": "Your machine:",
        "helper_dl": "1. Download PDF:",
        "helper_site": "Official Site",
        "helper_drag": "2. Drop it below 👇",
        "pdf_drop_label": "Manual PDF File",
        "style_label": "🧠 Pedagogical Approach",
        "memory_label": "💾 Learning Continuity",
        "memory_upload": "Resume session (.txt)",
        "memory_download": "Save my notes",
        "reset": "🗑️ New Session",
        "about_title": "ℹ️ Project Philosophy",
        "about_text": "**Groovebox Tutor** is a free project, born from the desire to reconnect musicians with their gear.\n\nOur goal isn't to copy, but to **understand**. The AI acts like a sound engineer sitting next to you: listening, reading the docs, and teaching you *how* to sculpt your own tone.\n\nThis tool is free. If it helps you learn, you can support its development.",
        "buy_coffee": "☕ Support the project (Donate)",
        "title": "Groovebox Tutor AI",
        "caption": "Your studio mentor. Understand synthesis. Master your gear.",
        "how_to": "👋 **Goal: Autonomy**\n1. Upload your instrument's **Manual**.\n2. Provide a **Sound** that inspires you.\n3. Your assistant analyzes the texture and teaches you **the technical steps** to recreate that vibe yourself.",
        "audio_title": "🎧 Audio Material",
        "audio_desc": "Analysis source (MP3, WAV, M4A).",
        "drop_label": "Drop audio file here",
        "legal_warning": "⚠️ *Educational analysis tool. Inspiration is legal, plagiarism is not.*",
        "active_track": "🎵 Analyzing:",
        "unknown_track": "Unknown",
        "manual_loaded": "Technical knowledge assimilated!",
        "memory_loaded": "Student context loaded!",
        "input_placeholder": "Ask your mentor...",
        "tones": ["🤙 Encouraging Mentor", "👔 Technical Expert", "⚡ Concise & Direct"],
        "formats": ["📝 Full Lesson", "✅ Checklist (Actionable)", "💬 Interactive Mode (Step-by-step)"],
        "sugg_combo": "🔥 Analyze sound & explain synthesis",
        "sugg_audio": "🥁 Deconstruct the rhythm",
        "sugg_pdf": "🎛️ What is this specific function?",
        "sugg_web": "🔍 I need a Sound Design technique",
        "theme_detected": "🎨 Vibe detected:",
        "apply_theme": "Apply Theme",
        "back_default": "🔙 Back to Default"
    },
    # (Les autres langues Espagnol/Allemand/etc restent sur le même modèle, 
    #  je peux te les générer si tu veux, mais pour l'instant ces 2 là suffisent pour comprendre la vision)
}
    },
    "Español 🇪🇸": {
        "settings": "Configuración",
        "api_help": "ℹ️ ¿Cómo obtener clave gratis?",
        "doc_label": "📂 **Documentación (Manual)**",
        "style_label": "🧠 Estilo del Profesor",
        "memory_label": "💾 Memoria / Sesión",
        "memory_upload": "Cargar sesión anterior",
        "memory_download": "Descargar historial",
        "reset": "🗑️ Reiniciar",
        "support": "❤️ Apoyar",
        "buy_coffee": "☕ Invítame un café",
        "title": "Groovebox Tutor AI",
        "caption": "Decodifica el sonido. Domina tu máquina. Crea tu propio tono.",
        "how_to": "👋 **¡Bienvenido!**\n1. Sube el **Manual PDF** (barra lateral).\n2. Arrastra un **Archivo de Audio** abajo.\n3. La IA analiza la textura, consulta el manual y explica **los conceptos técnicos** para lograr este estilo (entender para crear).",
        "audio_title": "🎧 Fuente de Audio",
        "audio_desc": "Sube un archivo de audio (MP3, WAV, M4A) para analizar.",
        "drop_label": "Arrastra tu archivo aquí",
        "active_track": "🎵 Pista activa:",
        "manual_loaded": "¡Manual cargado!",
        "memory_loaded": "¡Memoria cargada!",
        "input_placeholder": "Escribe tu pregunta aquí...",
        "tones": ["🤙 Genial y Pedagógico", "👔 Experto Técnico", "⚡ Breve y Directo"],
        "formats": ["📝 Tutorial Completo", "✅ Lista de verificación", "💬 Interactivo (Paso a paso)"],
        "sugg_combo": "🔥 Decodifica este sonido y dame la receta",
        "sugg_audio": "🥁 Analiza el ritmo",
        "sugg_pdf": "🎛️ Explícame una función oculta",
        "sugg_web": "🔍 Encuentra un truco de diseño sonoro",
        "theme_detected": "🎨 Ambiente detectado:",
        "apply_theme": "Aplicar tema",
        "back_default": "🔙 Volver al defecto"
    },
    "Deutsch 🇩🇪": {
        "settings": "Einstellungen",
        "api_help": "ℹ️ Kostenlosen Key erhalten?",
        "doc_label": "📂 **Dokumentation (Handbuch)**",
        "style_label": "🧠 Lehrer-Stil",
        "memory_label": "💾 Speicher / Sitzung",
        "memory_upload": "Sitzung laden",
        "memory_download": "Verlauf herunterladen",
        "reset": "🗑️ Zurücksetzen",
        "support": "❤️ Unterstützen",
        "buy_coffee": "☕ Spendier mir einen Kaffee",
        "title": "Groovebox Tutor AI",
        "caption": "Entschlüssle den Sound. Beherrsche deine Maschine.",
        "how_to": "👋 **Willkommen!**\n1. Lade das **PDF-Handbuch** (links).\n2. Lade eine **Audiodatei** hoch (unten).\n3. Die KI analysiert die Textur, prüft das Handbuch und erklärt **die technischen Konzepte**, um diesen Stil zu erreichen (Verstehen statt Kopieren).",
        "audio_title": "🎧 Audioquelle",
        "audio_desc": "Lade eine Audiodatei (MP3, WAV, M4A) zur Analyse hoch.",
        "drop_label": "Datei hier ablegen",
        "active_track": "🎵 Aktiver Track:",
        "manual_loaded": "Handbuch geladen!",
        "memory_loaded": "Speicher geladen!",
        "input_placeholder": "Stelle hier deine Frage...",
        "tones": ["🤙 Cool & Pädagogisch", "👔 Technischer Experte", "⚡ Kurz & Direkt"],
        "formats": ["📝 Vollständiges Tutorial", "✅ Checkliste (Schritt für Schritt)", "💬 Interaktiv (Schrittweise)"],
        "sugg_combo": "🔥 Entschlüssle diesen Sound + Rezept",
        "sugg_audio": "🥁 Analysiere den Groove",
        "sugg_pdf": "🎛️ Erkläre eine versteckte Funktion",
        "sugg_web": "🔍 Finde einen Sound-Design-Tipp",
        "theme_detected": "🎨 Stimmung erkannt:",
        "apply_theme": "Thema anwenden",
        "back_default": "🔙 Zurück zum Standard"
    },
    "Italiano 🇮🇹": {
        "settings": "Impostazioni",
        "api_help": "ℹ️ Come avere una chiave gratis?",
        "doc_label": "📂 **Documentazione (Manuale)**",
        "style_label": "🧠 Stile del Tutor",
        "memory_label": "💾 Memoria / Sessione",
        "memory_upload": "Carica sessione",
        "memory_download": "Scarica cronologia",
        "reset": "🗑️ Reset",
        "support": "❤️ Supporta",
        "buy_coffee": "☕ Offrimi un caffè",
        "title": "Groovebox Tutor AI",
        "caption": "Decodifica il suono. Padroneggia la macchina.",
        "how_to": "👋 **Benvenuto!**\n1. Carica il **Manuale PDF** (a sinistra).\n2. Trascina un **File Audio** qui sotto.\n3. L'IA analizza la struttura, consulta il manuale e spiega **i concetti tecnici** per ottenere questo stile (capire per creare).",
        "audio_title": "🎧 Sorgente Audio",
        "audio_desc": "Carica un file audio (MP3, WAV) per analizzarlo.",
        "drop_label": "Trascina qui il file",
        "active_track": "🎵 Traccia attiva:",
        "manual_loaded": "Manuale caricato!",
        "memory_loaded": "Memoria caricata!",
        "input_placeholder": "Fai la tua domanda qui...",
        "tones": ["🤙 Cool & Pedagogico", "👔 Esperto Tecnico", "⚡ Breve & Diretto"],
        "formats": ["📝 Tutorial Completo", "✅ Checklist (Passo dopo passo)", "💬 Interattivo (Uno step alla volta)"],
        "sugg_combo": "🔥 Decodifica suono + Ricetta",
        "sugg_audio": "🥁 Analizza il groove",
        "sugg_pdf": "🎛️ Spiegami una funzione nascosta",
        "sugg_web": "🔍 Trova un trucco di Sound Design",
        "theme_detected": "🎨 Atmosfera rilevata:",
        "apply_theme": "Applica tema",
        "back_default": "🔙 Torna al default"
    },
    "Português 🇧🇷": {
        "settings": "Configurações",
        "api_help": "ℹ️ Como obter chave grátis?",
        "doc_label": "📂 **Documentação (Manual)**",
        "style_label": "🧠 Estilo do Professor",
        "memory_label": "💾 Memória / Sessão",
        "memory_upload": "Carregar sessão",
        "memory_download": "Baixar histórico",
        "reset": "🗑️ Reset",
        "support": "❤️ Apoiar",
        "buy_coffee": "☕ Me paga um café",
        "title": "Groovebox Tutor AI",
        "caption": "Decodifique o som. Domine sua máquina.",
        "how_to": "👋 **Bem-vindo!**\n1. Envie o **Manual PDF** (à esquerda).\n2. Arraste um **Arquivo de Áudio** abaixo.\n3. A IA analisa a textura, consulta o manual e explica **os conceitos técnicos** para atingir esse estilo (entender para criar).",
        "audio_title": "🎧 Fonte de Áudio",
        "audio_desc": "Envie um arquivo de áudio (MP3, WAV) para análise.",
        "drop_label": "Arraste seu arquivo aqui",
        "active_track": "🎵 Faixa ativa:",
        "manual_loaded": "Manual carregado!",
        "memory_loaded": "Memória carregada!",
        "input_placeholder": "Faça sua pergunta aqui...",
        "tones": ["🤙 Legal e Pedagógico", "👔 Especialista Técnico", "⚡ Curto e Direto"],
        "formats": ["📝 Tutorial Completo", "✅ Checklist (Passo a passo)", "💬 Interativo (Um passo de cada vez)"],
        "sugg_combo": "🔥 Decodifique esse som + Receita",
        "sugg_audio": "🥁 Analise o groove",
        "sugg_pdf": "🎛️ Explique uma função oculta",
        "sugg_web": "🔍 Dica de Sound Design",
        "theme_detected": "🎨 Vibe detectada:",
        "apply_theme": "Aplicar tema",
        "back_default": "🔙 Voltar ao padrão"
    },
    "日本語 (Japonais) 🇯🇵": {
        "settings": "設定",
        "api_help": "ℹ️ 無料APIキーの取得方法",
        "doc_label": "📂 **ドキュメント (マニュアル)**",
        "style_label": "🧠 先生のスタイル",
        "memory_label": "💾 メモリ / セッション",
        "memory_upload": "セッションをロード",
        "memory_download": "履歴をダウンロード",
        "reset": "🗑️ リセット",
        "support": "❤️ 応援する",
        "buy_coffee": "☕ コーヒーを奢る",
        "title": "Groovebox Tutor AI",
        "caption": "音を解読し、マシンをマスターしよう。",
        "how_to": "👋 **ようこそ！**\n1. 左のメニューから**PDFマニュアル**をアップロード。\n2. 下に**オーディオファイル**をドロップ。\n3. AIが音の質感を分析し、マニュアルを参照して、そのスタイルに近づけるための**技術的な概念**を説明します（コピーではなく、創造のために）。",
        "audio_title": "🎧 音源",
        "audio_desc": "分析するオーディオファイル(MP3, WAV)をアップロード。",
        "drop_label": "ここにファイルをドロップ",
        "active_track": "🎵 再生中:",
        "manual_loaded": "マニュアル読み込み完了!",
        "memory_loaded": "メモリ読み込み完了!",
        "input_placeholder": "ここに質問を入力してください...",
        "tones": ["🤙 フレンドリー＆丁寧", "👔 技術エキスパート", "⚡ 短く簡潔に"],
        "formats": ["📝 完全チュートリアル", "✅ チェックリスト (手順)", "💬 インタラクティブ (一歩ずつ)"],
        "sugg_combo": "🔥 この音を再現する方法を教えて",
        "sugg_audio": "🥁 グルーヴを分析して",
        "sugg_pdf": "🎛️ 隠し機能を教えて",
        "sugg_web": "🔍 サウンドデザインのコツを探す",
        "theme_detected": "🎨 雰囲気を検出:",
        "apply_theme": "テーマを適用",
        "back_default": "🔙 デフォルトに戻す"
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
    # 1. Langue
    lang = st.selectbox("Language / Langue 🌍", list(TR.keys()), index=0)
    T = TR.get(lang, TR["Français 🇫🇷"]) # Fallback
    
    # 2. Settings (Avec explication pédagogique sur la clé)
    st.title(T["settings"])
    
    api_key = st.text_input(T["api_label"], type="password")
    with st.expander(T["api_help"]):
        st.markdown(f"""
        1. [Google AI Studio](https://aistudio.google.com/) (Get API Key).
        2. {T['api_desc']}
        """)
    
    st.markdown("---")
    
    # 3. Philosophie & Don (NOUVEAU BLOC)
    with st.expander(T["about_title"], expanded=False):
        st.markdown(T["about_text"])
        st.link_button(T["buy_coffee"], "https://www.buymeacoffee.com/", use_container_width=True)
    
    st.markdown("---")

    # 4. Personnalisation
    st.markdown(f"### {T['style_label']}")
    style_tone = st.selectbox("Tone", T["tones"], index=0, label_visibility="collapsed")
    style_format = st.radio("Format", T["formats"], index=0, label_visibility="collapsed")

    # 5. Mémoire
    st.markdown("---")
    st.markdown(f"### {T['memory_label']}")
    
    uploaded_memory = st.file_uploader(T["memory_upload"], type=["txt"], key="mem_up", label_visibility="collapsed")
    if uploaded_memory:
        st.session_state.memory_content = uploaded_memory.getvalue().decode("utf-8")
        st.success(T["memory_loaded"])
    
    if "chat_history" in st.session_state and st.session_state.chat_history:
        history_txt = format_history_for_download(st.session_state.chat_history)
        st.download_button(
            label=f"📥 {T['memory_download']}",
            data=history_txt,
            file_name=f"groovebox_mentor_session_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    # 6. Documentation Helper
    st.markdown("---")
    st.info(T["doc_label"])
    
    with st.expander(T["helper_title"]):
        # (Garde ton dictionnaire MANUAL_LINKS ici, je l'abrège pour la lisibilité)
        MANUAL_LINKS = {"Elektron Digitakt II": "https://www.elektron.se/en/support-downloads/digitakt-ii", "Roland SP-404 MKII": "https://www.roland.com/..."}
        selected_machine = st.selectbox(T["helper_machine"], list(MANUAL_LINKS.keys()))
        st.markdown(T["helper_dl"])
        st.link_button(f"⬇️ {selected_machine} - {T['helper_site']}", MANUAL_LINKS[selected_machine], use_container_width=True)
        st.markdown(T["helper_drag"])

    uploaded_pdf = st.file_uploader(T["pdf_drop_label"], type=["pdf"], label_visibility="collapsed")
    
    # 7. Reset en bas
    st.markdown("---")
    if st.button(T["reset"], type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- MAIN PAGE ---
st.title(f"🎹 {T['title']}")
st.caption(T["caption"])

# --- MAIN PAGE ---
st.title(f"🎹 {T['title']}")
st.caption(T["caption"])

# --- EXPLICATION RAPIDE (HOW TO) ---
st.info(T["how_to"])

# --- AUDIO ZONE ---
with st.container(border=True):
    st.subheader(T["audio_title"])
    st.markdown(T["audio_desc"])
    
    uploaded_audio = st.file_uploader(T["drop_label"], type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    
    # DISCLAIMER LEGAL
    if not uploaded_audio:
        st.caption("⚠️ *Usage strictement personnel et pédagogique. Respectez le droit d'auteur.*")

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