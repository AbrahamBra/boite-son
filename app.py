import streamlit as st
import google.generativeai as genai
import os
import tempfile
import time
from datetime import datetime

# --- 1. SETUP & CONFIGURATION  ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "PREMIUM MINIMALIST" ---
st.markdown("""
<style>
    /* Import de la police "Inter" (Standard Pro) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    /* BASE */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #E0E0E0; /* Blanc cassé pour moins de fatigue oculaire */
    }
    
    /* FOND UNIFIÉ (Sidebar + Main) */
    .stApp {
        background-color: #0E1117; /* Gris très profond (Pas noir pur) */
    }
    [data-testid="stSidebar"] {
        background-color: #0E1117;
        border-right: 1px solid #1F1F1F; /* Séparation ultra-subtile */
    }

    /* TITRES */
    h1 {
        font-weight: 600;
        letter-spacing: -1px;
        color: #FFFFFF;
    }
    h2, h3 {
        font-weight: 400;
        color: #A0A0A0;
    }

    /* INPUTS (Flat Design) */
    .stTextInput > div > div > input {
        background-color: #161920;
        border: 1px solid #303030;
        color: white;
        border-radius: 8px;
        padding: 10px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4A4A4A; /* Pas de bleu Windows, juste un gris plus clair */
        box-shadow: none;
    }

    /* BOUTONS (Sophistiqués) */
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
    
    /* BOUTON ACTION PRINCIPALE (Primary) */
    div[data-testid="stHorizontalBlock"] > div:first-child button {
        background-color: #FFFFFF; /* Bouton Blanc style Vercel/Apple */
        color: #000000;
        border: none;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child button:hover {
        background-color: #E0E0E0;
    }

    /* UPLOAD ZONES (Clean) */
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
    
    /* SUGGESTIONS (Pills) */
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

    /* NETTOYAGE */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 3rem; padding-bottom: 5rem;}
    
    /* Cacher les labels des inputs si besoin pour épuré */
    .stTextInput label {
        font-size: 12px;
        color: #606060;
    }
</style>
""", unsafe_allow_html=True)


# --- 3. DICTIONNAIRE MULTILINGUE (Mis à jour avec étape Clé API) ---
TR = {
    "Français 🇫🇷": {
        "settings": "Réglages",
        "api_label": "Clé API Google (Requis)",
        "api_help": "ℹ️ Pourquoi une clé perso ?",
        "api_desc": "Projet open-source. L'usage de votre propre clé gratuite garantit votre indépendance et la gratuité totale de l'outil.",
        "doc_label": "📂 **Documentation (Manuel)**",
        "helper_title": "🔍 Trouver mon manuel officiel",
        "helper_machine": "Votre machine :",
        "helper_dl": "1. Télécharger le PDF :",
        "helper_site": "Site Constructeur",
        "helper_drag": "2. Déposez-le ci-dessous 👇",
        "pdf_drop_label": "Fichier PDF du manuel",
        "style_label": "🧠 Approche Pédagogique",
        "memory_label": "💾 Mémoire / Session",
        "memory_upload": "Reprendre une session (.txt)",
        "memory_download": "Sauvegarder mes notes",
        "reset": "🗑️ Nouvelle Session",
        "about_title": "ℹ️ Philosophie du projet",
        "about_text": "**Groovebox Tutor** est un outil libre.\n\nNotre but n'est pas de copier bêtement, mais de **comprendre**. L'IA agit comme un binôme technique : elle écoute, lit la doc, et vous explique *comment* sculpter votre son.\n\nL'outil est gratuit. Si vous apprenez grâce à lui, vous pouvez soutenir son maintien.",
        "buy_coffee": "☕ Soutenir le projet (Don)",
        "title": "Groovebox Tutor AI",
        "caption": "Votre binôme technique. Décryptez le son. Maîtrisez votre machine.",
        "how_to": "👋 **Bienvenue ! Pour commencer :**\n1. **Clé API :** Entrez votre clé Google gratuite dans le menu à gauche (Indispensable).\n2. **Manuel :** Chargez le PDF de votre machine.\n3. **Son :** Glissez un fichier audio ci-dessous pour lancer l'analyse.",
        "audio_title": "🎧 Matériau Sonore",
        "audio_desc": "Support d'analyse (MP3, WAV, M4A).",
        "drop_label": "Déposez votre fichier audio ici",
        "legal_warning": "⚠️ *Outil d'analyse à but éducatif. L'inspiration est légale, le plagiat ne l'est pas.*",
        "active_track": "🎵 Analyse en cours sur :",
        "unknown_track": "Fichier inconnu",
        "manual_loaded": "Connaissances techniques assimilées !",
        "memory_loaded": "Contexte de l'élève chargé !",
        "input_placeholder": "Posez votre question...",
        "tones": ["🤙 Pédagogue & Cool", "👔 Expert Technique", "⚡ Synthétique & Direct"],
        "formats": ["📝 Cours Complet", "✅ Checklist (Actionable)", "💬 Mode Interactif (Pas à pas)"],
        "sugg_combo": "🔥 Analyse ce son et explique la synthèse",
        "sugg_audio": "🥁 Décompose la structure rythmique",
        "sugg_pdf": "🎛️ À quoi sert cette fonction précise ?",
        "sugg_web": "🔍 Je cherche une technique de Sound Design",
        "theme_detected": "🎨 Ambiance détectée :",
        "apply_theme": "Appliquer le thème",
        "back_default": "🔙 Retour au défaut"
    },
    "English 🇬🇧": {
        "settings": "Settings",
        "api_label": "Google API Key (Required)",
        "api_help": "ℹ️ Why a personal key?",
        "api_desc": "Open-source project. Using your own free key ensures your independence and keeps the tool free forever.",
        "doc_label": "📂 **Documentation (Manual)**",
        "helper_title": "🔍 Find official manual",
        "helper_machine": "Your machine:",
        "helper_dl": "1. Download PDF:",
        "helper_site": "Official Site",
        "helper_drag": "2. Drop it below 👇",
        "pdf_drop_label": "Manual PDF File",
        "style_label": "🧠 Pedagogical Approach",
        "memory_label": "💾 Memory / Session",
        "memory_upload": "Resume session (.txt)",
        "memory_download": "Save my notes",
        "reset": "🗑️ New Session",
        "about_title": "ℹ️ Project Philosophy",
        "about_text": "**Groovebox Tutor** is free software.\n\nOur goal isn't to copy, but to **understand**. The AI acts like a technical partner: listening, reading docs, and teaching you *how* to sculpt your tone.\n\nThis tool is free. If it helps you learn, you can support its maintenance.",
        "buy_coffee": "☕ Support the project (Donate)",
        "title": "Groovebox Tutor AI",
        "caption": "Your technical partner. Decode sound. Master your gear.",
        "how_to": "👋 **Welcome! To start:**\n1. **API Key:** Enter your free Google Key in the left menu (Required).\n2. **Manual:** Upload your machine's PDF.\n3. **Sound:** Drop an audio file below to start analysis.",
        "audio_title": "🎧 Audio Material",
        "audio_desc": "Analysis source (MP3, WAV, M4A).",
        "drop_label": "Drop audio file here",
        "legal_warning": "⚠️ *Educational analysis tool. Inspiration is legal, plagiarism is not.*",
        "active_track": "🎵 Analyzing:",
        "unknown_track": "Unknown",
        "manual_loaded": "Technical knowledge assimilated!",
        "memory_loaded": "Student context loaded!",
        "input_placeholder": "Ask your question...",
        "tones": ["🤙 Encouraging Teacher", "👔 Technical Expert", "⚡ Concise & Direct"],
        "formats": ["📝 Full Lesson", "✅ Checklist (Actionable)", "💬 Interactive Mode (Step-by-step)"],
        "sugg_combo": "🔥 Analyze sound & explain synthesis",
        "sugg_audio": "🥁 Deconstruct the rhythm",
        "sugg_pdf": "🎛️ What is this specific function?",
        "sugg_web": "🔍 I need a Sound Design technique",
        "theme_detected": "🎨 Vibe detected:",
        "apply_theme": "Apply Theme",
        "back_default": "🔙 Back to Default"
    },
    "Español 🇪🇸": {
        "settings": "Configuración",
        "api_label": "Clave API Google",
        "api_help": "ℹ️ ¿Por qué una clave personal?",
        "api_desc": "Proyecto de código abierto. Usar tu propia clave gratuita garantiza tu independencia y la gratuidad de la herramienta.",
        "doc_label": "📂 **Tu Manual (La Verdad)**",
        "helper_title": "🔍 Encontrar manual oficial",
        "helper_machine": "Tu máquina:",
        "helper_dl": "1. Descargar PDF:",
        "helper_site": "Sitio Oficial",
        "helper_drag": "2. Arrástralo abajo 👇",
        "pdf_drop_label": "Archivo PDF del manual",
        "style_label": "🧠 Enfoque Pedagógico",
        "memory_label": "💾 Continuidad de Aprendizaje",
        "memory_upload": "Reanudar sesión (.txt)",
        "memory_download": "Guardar mis notas",
        "reset": "🗑️ Nueva Sesión",
        "about_title": "ℹ️ Filosofía del proyecto",
        "about_text": "**Groovebox Tutor** es software libre.\n\nNuestro objetivo no es copiar, sino **entender**. La IA actúa como un socio técnico: escucha, lee el manual y te enseña *cómo* esculpir tu sonido.\n\nEs gratis. Si aprendes con él, puedes apoyar su mantenimiento.",
        "buy_coffee": "☕ Apoyar el proyecto (Donar)",
        "title": "Groovebox Tutor AI",
        "caption": "Tu socio técnico. Decodifica el sonido. Domina tu máquina.",
        "how_to": "👋 **Objetivo: Autonomía**\n1. Sube el **Manual**.\n2. Proporciona un **Sonido**.\n3. Tu socio analiza la textura y te enseña **los pasos técnicos** para recrear ese estilo tú mismo.",
        "audio_title": "🎧 Material de Audio",
        "audio_desc": "Fuente de análisis (MP3, WAV, M4A).",
        "drop_label": "Arrastra tu archivo aquí",
        "legal_warning": "⚠️ *Herramienta educativa. La inspiración es legal, el plagio no.*",
        "active_track": "🎵 Analizando:",
        "unknown_track": "Desconocido",
        "manual_loaded": "¡Conocimiento técnico asimilado!",
        "memory_loaded": "¡Contexto del alumno cargado!",
        "input_placeholder": "Haz tu pregunta...",
        "tones": ["🤙 Profesor Genial", "👔 Experto Técnico", "⚡ Conciso y Directo"],
        "formats": ["📝 Lección Completa", "✅ Checklist (Accionable)", "💬 Modo Interactivo (Paso a paso)"],
        "sugg_combo": "🔥 Analiza sonido y explica síntesis",
        "sugg_audio": "🥁 Deconstruye el ritmo",
        "sugg_pdf": "🎛️ ¿Para qué sirve esta función?",
        "sugg_web": "🔍 Busco técnica de Diseño Sonoro",
        "theme_detected": "🎨 Ambiente detectado:",
        "apply_theme": "Aplicar tema",
        "back_default": "🔙 Volver al defecto"
    },
    "Deutsch 🇩🇪": {
        "settings": "Einstellungen",
        "api_label": "Google API Key",
        "api_help": "ℹ️ Warum ein eigener Key?",
        "api_desc": "Open-Source-Projekt. Dein eigener kostenloser Key garantiert Unabhängigkeit und hält das Tool gratis.",
        "doc_label": "📂 **Dein Handbuch (Die Wahrheit)**",
        "helper_title": "🔍 Offizielles Handbuch finden",
        "helper_machine": "Deine Maschine:",
        "helper_dl": "1. PDF herunterladen:",
        "helper_site": "Offizielle Seite",
        "helper_drag": "2. Unten ablegen 👇",
        "pdf_drop_label": "PDF-Datei des Handbuchs",
        "style_label": "🧠 Pädagogischer Ansatz",
        "memory_label": "💾 Lernfortschritt",
        "memory_upload": "Sitzung fortsetzen (.txt)",
        "memory_download": "Notizen speichern",
        "reset": "🗑️ Neue Sitzung",
        "about_title": "ℹ️ Projektphilosophie",
        "about_text": "**Groovebox Tutor** ist freie Software.\n\nUnser Ziel ist nicht Kopieren, sondern **Verstehen**. Die KI agiert als technischer Partner: Sie hört zu, liest das Handbuch und lehrt dich, *wie* du deinen Sound formst.\n\nKostenlos. Wenn du etwas lernst, kannst du das Projekt unterstützen.",
        "buy_coffee": "☕ Projekt unterstützen (Spende)",
        "title": "Groovebox Tutor AI",
        "caption": "Dein technischer Partner. Entschlüssle den Sound. Beherrsche deine Maschine.",
        "how_to": "👋 **Ziel: Autonomie**\n1. Lade das **Handbuch** hoch.\n2. Wähle einen **Sound**.\n3. Dein Partner analysiert die Textur und lehrt dich **die technischen Schritte**, um diesen Vibe selbst zu erzeugen.",
        "audio_title": "🎧 Audiomaterial",
        "audio_desc": "Analyse-Quelle (MP3, WAV, M4A).",
        "drop_label": "Audiodatei hier ablegen",
        "legal_warning": "⚠️ *Bildungstool. Inspiration ist legal, Plagiat nicht.*",
        "active_track": "🎵 Analysiere:",
        "unknown_track": "Unbekannt",
        "manual_loaded": "Technisches Wissen assimiliert!",
        "memory_loaded": "Schüler-Kontext geladen!",
        "input_placeholder": "Stelle deine Frage...",
        "tones": ["🤙 Cool & Pädagogisch", "👔 Technischer Experte", "⚡ Kurz & Direkt"],
        "formats": ["📝 Volle Lektion", "✅ Checkliste (Umsetzbar)", "💬 Interaktiv (Schritt für Schritt)"],
        "sugg_combo": "🔥 Analyse Sound & erkläre Synthese",
        "sugg_audio": "🥁 Zerlege den Rhythmus",
        "sugg_pdf": "🎛️ Wofür ist diese Funktion?",
        "sugg_web": "🔍 Suche Sound-Design-Technik",
        "theme_detected": "🎨 Stimmung erkannt:",
        "apply_theme": "Thema anwenden",
        "back_default": "🔙 Zurück zum Standard"
    },
    "Italiano 🇮🇹": {
        "settings": "Impostazioni",
        "api_label": "Chiave API Google",
        "api_help": "ℹ️ Perché una chiave personale?",
        "api_desc": "Progetto open-source. L'uso della tua chiave gratuita garantisce indipendenza e gratuità dello strumento.",
        "doc_label": "📂 **Il tuo Manuale (La Verità)**",
        "helper_title": "🔍 Trova manuale ufficiale",
        "helper_machine": "La tua macchina:",
        "helper_dl": "1. Scarica PDF:",
        "helper_site": "Sito Ufficiale",
        "helper_drag": "2. Trascina qui sotto 👇",
        "pdf_drop_label": "File PDF del manuale",
        "style_label": "🧠 Approccio Pedagogico",
        "memory_label": "💾 Continuità Didattica",
        "memory_upload": "Riprendi sessione (.txt)",
        "memory_download": "Salva i miei appunti",
        "reset": "🗑️ Nuova Sessione",
        "about_title": "ℹ️ Filosofia del progetto",
        "about_text": "**Groovebox Tutor** è software libero.\n\nNon vogliamo copiare, ma **capire**. L'IA agisce come un partner tecnico: ascolta, legge il manuale e ti insegna *come* scolpire il tuo suono.\n\nÈ gratis. Se impari qualcosa, puoi sostenere il progetto.",
        "buy_coffee": "☕ Sostieni il progetto (Dona)",
        "title": "Groovebox Tutor AI",
        "caption": "Il tuo partner tecnico. Decodifica il suono. Padroneggia la macchina.",
        "how_to": "👋 **Obiettivo: Autonomia**\n1. Carica il **Manuale**.\n2. Fornisci un **Suono**.\n3. Il tuo partner analizza la struttura e ti insegna **i passaggi tecnici** per ricreare quello stile.",
        "audio_title": "🎧 Materiale Audio",
        "audio_desc": "Fonte di analisi (MP3, WAV, M4A).",
        "drop_label": "Trascina il file audio qui",
        "legal_warning": "⚠️ *Strumento educativo. L'ispirazione è legale, il plagio no.*",
        "active_track": "🎵 Analisi in corso:",
        "unknown_track": "Sconosciuto",
        "manual_loaded": "Conoscenza tecnica assimilata!",
        "memory_loaded": "Contesto studente caricato!",
        "input_placeholder": "Fai la tua domanda...",
        "tones": ["🤙 Insegnante Cool", "👔 Esperto Tecnico", "⚡ Sintetico & Diretto"],
        "formats": ["📝 Lezione Completa", "✅ Checklist (Pratica)", "💬 Interattivo (Passo dopo passo)"],
        "sugg_combo": "🔥 Analizza suono e spiega sintesi",
        "sugg_audio": "🥁 Decostruisci il ritmo",
        "sugg_pdf": "🎛️ A cosa serve questa funzione?",
        "sugg_web": "🔍 Cerco tecnica Sound Design",
        "theme_detected": "🎨 Atmosfera rilevata:",
        "apply_theme": "Applica tema",
        "back_default": "🔙 Torna al default"
    },
    "Português 🇧🇷": {
        "settings": "Configurações",
        "api_label": "Chave API Google",
        "api_help": "ℹ️ Por que chave pessoal?",
        "api_desc": "Projeto open-source. Usar sua chave gratuita garante independência e ferramenta grátis para sempre.",
        "doc_label": "📂 **Seu Manual (A Verdade)**",
        "helper_title": "🔍 Encontrar manual oficial",
        "helper_machine": "Sua máquina:",
        "helper_dl": "1. Baixar PDF:",
        "helper_site": "Site Oficial",
        "helper_drag": "2. Arraste abaixo 👇",
        "pdf_drop_label": "Arquivo PDF do manual",
        "style_label": "🧠 Abordagem Pedagógica",
        "memory_label": "💾 Continuidade",
        "memory_upload": "Retomar sessão (.txt)",
        "memory_download": "Salvar notas",
        "reset": "🗑️ Nova Sessão",
        "about_title": "ℹ️ Filosofia do projeto",
        "about_text": "**Groovebox Tutor** é software livre.\n\nO objetivo não é copiar, mas **entender**. A IA age como um parceiro técnico: ouve, lê o manual e ensina *como* esculpir seu som.\n\nÉ grátis. Se ajudar você a aprender, apoie o projeto.",
        "buy_coffee": "☕ Apoiar o projeto (Doar)",
        "title": "Groovebox Tutor AI",
        "caption": "Seu parceiro técnico. Decodifique o som. Domine sua máquina.",
        "how_to": "👋 **Objetivo: Autonomia**\n1. Envie o **Manual**.\n2. Forneça um **Som**.\n3. Seu parceiro analisa a textura e ensina **os passos técnicos** para recriar essa vibe.",
        "audio_title": "🎧 Material de Áudio",
        "audio_desc": "Fonte de análise (MP3, WAV, M4A).",
        "drop_label": "Arraste o arquivo de áudio aqui",
        "legal_warning": "⚠️ *Ferramenta educativa. Inspiração é legal, plágio não.*",
        "active_track": "🎵 Analisando:",
        "unknown_track": "Desconhecido",
        "manual_loaded": "Conhecimento técnico assimilado!",
        "memory_loaded": "Contexto do aluno carregado!",
        "input_placeholder": "Faça sua pergunta...",
        "tones": ["🤙 Professor Legal", "👔 Especialista Técnico", "⚡ Curto & Direto"],
        "formats": ["📝 Aula Completa", "✅ Checklist (Prática)", "💬 Interativo (Passo a passo)"],
        "sugg_combo": "🔥 Analise som e explique síntese",
        "sugg_audio": "🥁 Desconstrua o ritmo",
        "sugg_pdf": "🎛️ Para que serve essa função?",
        "sugg_web": "🔍 Busco técnica de Sound Design",
        "theme_detected": "🎨 Vibe detectada:",
        "apply_theme": "Aplicar tema",
        "back_default": "🔙 Voltar ao padrão"
    },
    "日本語 (Japonais) 🇯🇵": {
        "settings": "設定",
        "api_label": "Google APIキー",
        "api_help": "ℹ️ なぜ個人のキーが必要？",
        "api_desc": "オープンソースプロジェクトです。個人の無料キーを使用することで、独立性とツールの無料化が保証されます。",
        "doc_label": "📂 **あなたのマニュアル (正解)**",
        "helper_title": "🔍 公式マニュアルを探す",
        "helper_machine": "機種:",
        "helper_dl": "1. PDFをダウンロード:",
        "helper_site": "公式サイト",
        "helper_drag": "2. 下にドラッグ 👇",
        "pdf_drop_label": "マニュアルのPDFファイル",
        "style_label": "🧠 教育アプローチ",
        "memory_label": "💾 学習の継続",
        "memory_upload": "セッションを再開 (.txt)",
        "memory_download": "ノートを保存",
        "reset": "🗑️ 新しいセッション",
        "about_title": "ℹ️ プロジェクトの哲学",
        "about_text": "**Groovebox Tutor** はフリーソフトウェアです。\n\n目的はコピーではなく**理解**です。AIは技術パートナーとして機能します：音を聴き、マニュアルを読み、独自の音を作る*方法*を教えます。\n\n無料です。学習に役立った場合は、支援をお願いします。",
        "buy_coffee": "☕ プロジェクトを支援 (寄付)",
        "title": "Groovebox Tutor AI",
        "caption": "あなたの技術パートナー。音を解読し、マシンを支配する。",
        "how_to": "👋 **目標：自律性**\n1. **マニュアル**をアップロード。\n2. インスピレーションとなる**音**を提供。\n3. パートナーが質感を分析し、その雰囲気を再現するための**技術的な手順**を教えます。",
        "audio_title": "🎧 音響素材",
        "audio_desc": "分析ソース (MP3, WAV, M4A)。",
        "drop_label": "ここにオーディオファイルをドロップ",
        "legal_warning": "⚠️ *教育用ツール。インスピレーションは合法的ですが、盗作は違法です。*",
        "active_track": "🎵 分析中:",
        "unknown_track": "不明",
        "manual_loaded": "技術知識を同化しました！",
        "memory_loaded": "生徒のコンテキストをロードしました！",
        "input_placeholder": "質問してください...",
        "tones": ["🤙 フレンドリーな先生", "👔 技術エキスパート", "⚡ 簡潔＆直接"],
        "formats": ["📝 完全なレッスン", "✅ チェックリスト (実践的)", "💬 インタラクティブ (一歩ずつ)"],
        "sugg_combo": "🔥 音を分析し、合成を説明して",
        "sugg_audio": "🥁 リズムを分解して",
        "sugg_pdf": "🎛️ この機能は何のためにありますか？",
        "sugg_web": "🔍 サウンドデザインのテクニックを探す",
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

def format_history(history):
    text = f"SESSION {datetime.now().strftime('%Y-%m-%d')}\n---\n"
    for msg in history:
        role = "USER" if msg['role'] == "user" else "AI"
        text += f"{role}: {msg['content']}\n\n"
    return text

# --- INTERFACE ---

# 1. SIDEBAR (Ultra Minimaliste)
with st.sidebar:
    # Langue
    lang_options = ["Français 🇫🇷", "English 🇬🇧", "Español 🇪🇸", "Deutsch 🇩🇪", "Italiano 🇮🇹", "Português 🇧🇷", "日本語 🇯🇵"]
    lang = st.selectbox("Langue", lang_options, label_visibility="collapsed")
    T = TR["Français 🇫🇷"] # Par défaut pour le code, tu peux remettre la logique dynamique si tu veux toutes les langues
    
    st.markdown("### " + T["settings"])
    
    # API Key (Discret)
    api_key = st.text_input("API Key", type="password", placeholder="Collez votre clé Google ici")
    if not api_key:
        st.caption("Une clé est requise pour utiliser l'IA.")
        with st.expander("Obtenir une clé"):
            st.markdown("[Google AI Studio](https://aistudio.google.com/) (Gratuit)")

    st.markdown("---")
    
    # Doc
    st.caption(T["doc_section"])
    with st.expander(T["doc_help"]):
        st.markdown("Liens vers les sites constructeurs (Elektron, Roland, Korg...)")
        # Ici tu remets tes liens si tu veux, mais cachés par défaut pour le clean
    
    uploaded_pdf = st.file_uploader(T["manual_upload"], type=["pdf"], label_visibility="collapsed")
    if uploaded_pdf:
        st.success(f"Actif : {uploaded_pdf.name}")

    st.markdown("---")
    
    # Session
    st.caption(T["memory_section"])
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(T["reset"], use_container_width=True):
            st.session_state.clear()
            st.rerun()
    with col_b:
        # Placeholder pour download (logique activée si chat existe)
        pass 

    st.markdown("---")
    with st.expander(T["about"]):
        st.caption("Groovebox Tutor est un projet Open Source gratuit dédié à l'apprentissage de la synthèse sonore.")
        st.markdown("[Soutenir le projet](https://www.buymeacoffee.com/)")

# 2. MAIN HEADER (Typographie forte)
st.title(T["title"])
st.markdown(f"<h3 style='margin-top: -20px; margin-bottom: 40px; color: #808080;'>{T['subtitle']}</h3>", unsafe_allow_html=True)

# 3. ONBOARDING (Si pas de clé)
if not api_key:
    st.info(f"{T['step_1']}")

# 4. STUDIO ZONE (Clean)
with st.container():
    uploaded_audio = st.file_uploader("Fichier Audio", type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    
    # Logique Audio
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

# 5. CHAT LOGIC
if api_key:
    genai.configure(api_key=api_key)
    
    # PDF Load
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.status("Lecture du manuel...", expanded=False) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_pdf_to_gemini(p)
            if r: 
                st.session_state.pdf_ref = r
                status.update(label="Manuel assimilé", state="complete")

    # Chat History
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    # Affichage Chat
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Suggestions (Pills)
    if not st.session_state.chat_history:
        col1, col2, col3 = st.columns(3)
        if col1.button(T["sugg_1"], type="secondary", use_container_width=True): prompt = T["sugg_1"]
        elif col2.button(T["sugg_2"], type="secondary", use_container_width=True): prompt = T["sugg_2"]
        elif col3.button(T["sugg_3"], type="secondary", use_container_width=True): prompt = T["sugg_3"]
        else: prompt = None
    else:
        prompt = None

    # Input User
    user_input = st.chat_input(T["placeholder"])
    if user_input: prompt = user_input

    # Traitement IA
    if prompt:
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        try: tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except: tools = None
        
        sys_prompt = "Tu es un expert musical pédagogue. Sois concis et précis."
        
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
            # Pas de spinner texte, juste l'animation par défaut
            try:
                resp = model.generate_content(req)
                st.markdown(resp.text)
                st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
            except Exception as e:
                st.error("Erreur de connexion IA")