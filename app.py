import streamlit as st
import google.generativeai as genai
import os
import tempfile
import yt_dlp
import time

# --- 1. CONFIGURATION GLOBALE ---
st.set_page_config(
    page_title="Groovebox Tutor AI",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE CSS "PRO / DARK MODE" ---
def local_css():
    st.markdown("""
    <style>
        /* Import d'une police 'Tech' */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono&display=swap');

        /* Fond global et textes */
        .stApp {
            background-color: #0E1117;
            font-family: 'Inter', sans-serif;
        }
        
        /* Titres */
        h1, h2, h3 {
            color: #FAFAFA !important;
            font-weight: 600;
        }

        /* Personnalisation de la Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #161B22;
            border-right: 1px solid #30363D;
        }
        
        /* Zone de Chat */
        .stChatMessage {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
        }
        
        /* Boutons (Style Hardware) */
        div.stButton > button {
            background-color: #238636;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #2EA043;
            box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
        }
        
        /* Bouton Reset (Rouge) */
        div.stButton > button[kind="primary"] {
            background-color: #DA3633;
        }

        /* Inputs textuels */
        .stTextInput > div > div > input {
            background-color: #0D1117;
            color: #C9D1D9;
            border: 1px solid #30363D;
        }

        /* Status Container (Loading) */
        .stStatus {
            background-color: #161B22;
            border: 1px solid #1F6FEB;
        }
        
        /* Cacher le menu Streamlit par défaut */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- 3. FONCTIONS LOGIQUES (Inchangées) ---

def download_audio_from_url(url):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
        # On ne met pas de spinner ici, on le gère dans l'UI avec st.status
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = info['ext']
            video_id = info['id']
            filename = f"{video_id}.{ext}"
            
            if os.path.exists(filename):
                return filename, info.get('title', 'Audio Web')
            return None, None
    except Exception as e:
        return None, None

def get_mime_type(filename):
    if filename.endswith('.mp3'): return 'audio/mp3'
    if filename.endswith('.wav'): return 'audio/wav'
    if filename.endswith('.m4a'): return 'audio/mp4'
    if filename.endswith('.webm'): return 'audio/webm'
    return 'audio/mp3'

def upload_to_gemini(path, mime_type):
    try:
        file_ref = genai.upload_file(path=path, mime_type=mime_type)
        while file_ref.state.name == "PROCESSING":
            time.sleep(1)
            file_ref = genai.get_file(file_ref.name)
        if file_ref.state.name == "FAILED": return None
        return file_ref
    except:
        return None

# --- 4. INTERFACE UTILISATEUR (UI) ---

# --- SIDEBAR (SETTINGS) ---
with st.sidebar:
    st.markdown("### 🎛️ Settings")
    api_key = st.text_input("Clé API Google", type="password", help="Ta clé AI Studio")
    
    st.markdown("---")
    st.markdown("### 📚 Documentation")
    uploaded_pdf = st.file_uploader("Manuel (PDF)", type=["pdf"], label_visibility="collapsed")
    if uploaded_pdf:
        st.caption(f"✅ {uploaded_pdf.name}")

    st.markdown("---")
    if st.button("🗑️ Reset Session", type="primary", use_container_width=True):
        st.session_state.chat_history = []
        if "audio_gemini_ref" in st.session_state: del st.session_state.audio_gemini_ref
        if "pdf_ref" in st.session_state: del st.session_state.pdf_ref
        if "current_audio_path" in st.session_state: del st.session_state.current_audio_path
        st.rerun()

# --- MAIN AREA ---

# En-tête stylisé
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("# 🎹")
with col_title:
    st.markdown("# Groovebox Tutor AI")
    st.markdown("*L'assistant pédagogique qui écoute tes sons et lit tes manuels.*")

st.markdown("---")

# Gestion de l'état (Initialisation)
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- ZONE AUDIO (CONTROL CENTER) ---
with st.container():
    st.markdown("### 🎧 Source Audio")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Option A : Lien Web**")
        url_input = st.text_input("YouTube / SoundCloud URL", label_visibility="collapsed", placeholder="https://youtube.com/...")
        if st.button("Charger le lien", use_container_width=True):
            if url_input:
                with st.status("🚀 Traitement de l'audio...", expanded=True) as status:
                    st.write("Téléchargement du flux...")
                    file_path, title = download_audio_from_url(url_input)
                    
                    if file_path:
                        st.write("Conversion terminée.")
                        st.session_state.current_audio_path = file_path
                        st.session_state.current_audio_name = title
                        # Reset Gemini ref
                        if "audio_gemini_ref" in st.session_state: del st.session_state.audio_gemini_ref
                        status.update(label="✅ Audio prêt !", state="complete", expanded=False)
                    else:
                        status.update(label="❌ Erreur de téléchargement", state="error")

    with col2:
        st.markdown("**Option B : Fichier Local**")
        uploaded_audio = st.file_uploader("MP3/WAV/M4A", type=["mp3", "wav", "m4a"], label_visibility="collapsed")
        if uploaded_audio:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                if "audio_gemini_ref" in st.session_state: del st.session_state.audio_gemini_ref

    # Lecteur Audio (S'il y a un son actif)
    if "current_audio_path" in st.session_state:
        st.success(f"🎵 Piste chargée : **{st.session_state.current_audio_name}**")
        st.audio(st.session_state.current_audio_path)

st.markdown("---")

# --- LOGIQUE BACKEND ---
if api_key:
    genai.configure(api_key=api_key)

    # 1. PDF Processor (Silencieux)
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.status("📘 Lecture du manuel...", expanded=False) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(uploaded_pdf.getvalue())
                pdf_path = tmp_pdf.name
            ref = upload_to_gemini(pdf_path, "application/pdf")
            if ref:
                st.session_state.pdf_ref = ref
                status.update(label="✅ Manuel mémorisé !", state="complete")

    # 2. Audio Processor (Silencieux)
    if "current_audio_path" in st.session_state and "audio_gemini_ref" not in st.session_state:
         with st.status("👂 Analyse du spectre audio...", expanded=False) as status:
            real_mime = get_mime_type(st.session_state.current_audio_path)
            ref = upload_to_gemini(st.session_state.current_audio_path, real_mime)
            if ref:
                st.session_state.audio_gemini_ref = ref
                status.update(label="✅ Audio analysé par l'IA !", state="complete")

    # --- ZONE DE CHAT ---
    st.markdown("### 💬 Conversation")
    
    # Affichage historique
    for message in st.session_state.chat_history:
        avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Input User
    if user_query := st.chat_input("Comment refaire ce kick ? À quoi sert ce bouton ?"):
        
        # Affichage question user
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_query)
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        # Prompt Pédagogique (Ton précédent)
        system_instruction = """
        Tu es un mentor musical passionné et pédagogue, expert en Grooveboxes.
        Ta mission n'est pas de lire le manuel à la place de l'utilisateur, mais de lui apprendre à comprendre sa machine.

        RÈGLES D'OR :
        1. 🧠 Vulgarise d'abord : Explique l'intention musicale (ex: "Pour donner du punch...").
        2. 🍎 Utilise des analogies simples.
        3. 📖 Guide, ne dicte pas : Utilise le PDF pour les boutons, mais ne noie pas sous les détails.
        4. ✨ Style : Encourageant, aéré, utilise le Markdown (Gras, Listes) pour structurer.
        
        Si tu dois expliquer un son : Analyse (Timbre/Effet) -> Recette (3 étapes) -> Manipulations (Boutons).
        """

        # Outils
        try:
            search_tool = genai.protos.Tool(google_search=genai.protos.GoogleSearch())
            tools_list = [search_tool]
        except:
            tools_list = None

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", 
            system_instruction=system_instruction,
            tools=tools_list
        )

        request_content = [user_query]
        if "pdf_ref" in st.session_state: request_content.append(st.session_state.pdf_ref)
        if "audio_gemini_ref" in st.session_state: 
            request_content.append(st.session_state.audio_gemini_ref)
            request_content.append("Analyse l'audio fourni.")

        # Génération avec feedback visuel
        with st.chat_message("assistant", avatar="🤖"):
            placeholder = st.empty()
            with st.spinner("Réflexion musicale..."):
                try:
                    response = model.generate_content(request_content)
                    placeholder.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    placeholder.error(f"Erreur : {e}")

else:
    # Message d'accueil si pas de clé API
    st.info("👈 Pour commencer, entre ta clé API Google dans le menu à gauche.")