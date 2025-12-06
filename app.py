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

# --- 3. DICTIONNAIRE MULTILINGUE (VERSION FINALE : ÉTHIQUE & LIBRE) ---
TR = {
    "Français 🇫🇷": {
        "settings": "Réglages",
        "api_label": "Clé API Google",
        "api_help": "ℹ️ Pourquoi une clé perso ?",
        "api_desc": "Projet open-source. L'usage de votre propre clé gratuite garantit votre indépendance et la gratuité totale de l'outil.",
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
        "about_text": "**Groovebox Tutor** est un outil libre.\n\nNotre but n'est pas de copier bêtement, mais de **comprendre**. L'IA agit comme un binôme technique : elle écoute, lit la doc, et vous explique *comment* sculpter votre son.\n\nL'outil est gratuit. Si vous apprenez grâce à lui, vous pouvez soutenir son maintien.",
        "buy_coffee": "☕ Soutenir le projet (Don)",
        "title": "Groovebox Tutor AI",
        "caption": "Votre binôme technique. Vous n'ouvrirez plus jamais votre documentation. L'IA facilite votre apprentissage.",
        "how_to": "👋 **Objectif : Autonomie**\n1. Importez le **Manuel**.\n2. Proposez un **Son** qui vous inspire.\n3. Votre binôme analyse la texture et vous enseigne **les étapes techniques** pour recréer ce grain vous-même.",
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
        "api_label": "Google API Key",
        "api_help": "ℹ️ Why a personal key?",
        "api_desc": "Open-source project. Using your own free key ensures your independence and keeps the tool free forever.",
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
        "about_text": "**Groovebox Tutor** is free software.\n\nOur goal isn't to copy, but to **understand**. The AI acts like a technical partner: listening, reading docs, and teaching you *how* to sculpt your tone.\n\nThis tool is free. If it helps you learn, you can support its maintenance.",
        "buy_coffee": "☕ Support the project (Donate)",
        "title": "Groovebox Tutor AI",
        "caption": "Your technical partner. Decode sound. Master your gear.",
        "how_to": "👋 **Goal: Autonomy**\n1. Upload the **Manual**.\n2. Provide a **Sound**.\n3. Your partner analyzes the texture and teaches you **the technical steps** to recreate that vibe yourself.",
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