import streamlit as st
import google.generativeai as genai
import os
import tempfile
import yt_dlp
import time

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="🎹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CORRECTIF (JUSTE POUR LE STYLE, PAS LES COULEURS DE FOND) ---
st.markdown("""
<style>
    /* Police plus moderne */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Style des boutons (Arrondis et propres) */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: 0.2s;
    }
    
    /* Bouton Principal (Vert) */
    div[data-testid="stHorizontalBlock"] > div:first-child button {
        background-color: #238636; 
        color: white;
    }

    /* Cacher les éléments parasites de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Nettoyage des paddings */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS (Inchangées) ---
def download_audio_from_url(url):
    try:
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': '%(id)s.%(ext)s', 'noplaylist': True, 'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"{info['id']}.{info['ext']}"
            if os.path.exists(filename): return filename, info.get('title', 'Audio Web')
            return None, None
    except: return None, None

def get_mime_type(filename):
    if filename.endswith('.m4a'): return 'audio/mp4'
    if filename.endswith('.wav'): return 'audio/wav'
    return 'audio/mp3'

def upload_to_gemini(path, mime_type):
    try:
        file_ref = genai.upload_file(path=path, mime_type=mime_type)
        while file_ref.state.name == "PROCESSING":
            time.sleep(1)
            file_ref = genai.get_file(file_ref.name)
        if file_ref.state.name == "FAILED": return None
        return file_ref
    except: return None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/7603/7603284.png", width=50)
    st.title("Settings")
    
    api_key = st.text_input("Clé API Google", type="password")
    
    st.info("📂 **Documentation**")
    uploaded_pdf = st.file_uploader("Manuel (PDF)", type=["pdf"], label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("🗑️ Reset tout", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- MAIN ---
col1, col2 = st.columns([5, 1])
with col1:
    st.title("Groovebox Tutor AI")
    st.caption("L'assistant qui écoute tes sons et t'explique comment les refaire.")

# --- ZONE AUDIO ---
with st.container(border=True):
    st.subheader("🎧 Source Audio")
    c1, c2 = st.columns(2)
    
    with c1:
        url_input = st.text_input("Lien YouTube", placeholder="Colle un lien ici...")
        if st.button("Charger le lien", use_container_width=True):
            if url_input:
                with st.status("Téléchargement...", expanded=True) as status:
                    f, t = download_audio_from_url(url_input)
                    if f:
                        st.session_state.current_audio_path = f
                        st.session_state.current_audio_name = t
                        if "audio_gemini_ref" in st.session_state: del st.session_state.audio_gemini_ref
                        status.update(label="✅ Prêt !", state="complete", expanded=False)
    
    with c2:
        uploaded_audio = st.file_uploader("Fichier Local", type=["mp3", "wav", "m4a"])
        if uploaded_audio:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                if "audio_gemini_ref" in st.session_state: del st.session_state.audio_gemini_ref

    if "current_audio_path" in st.session_state:
        st.audio(st.session_state.current_audio_path)
        st.caption(f"Piste active : {st.session_state.get('current_audio_name', 'Inconnu')}")

# --- LOGIC ---
if api_key:
    genai.configure(api_key=api_key)
    
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.spinner("Lecture du manuel..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_to_gemini(p, "application/pdf")
            if r: st.session_state.pdf_ref = r; st.toast("Manuel chargé !", icon="📘")

    if "current_audio_path" in st.session_state and "audio_gemini_ref" not in st.session_state:
        with st.spinner("Analyse audio..."):
            r = upload_to_gemini(st.session_state.current_audio_path, get_mime_type(st.session_state.current_audio_path))
            if r: st.session_state.audio_gemini_ref = r; st.toast("Audio analysé !", icon="🎹")

    # --- CHAT ---
    st.divider()
    
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if q := st.chat_input("Comment faire ce son ?"):
        with st.chat_message("user"): st.markdown(q)
        st.session_state.chat_history.append({"role": "user", "content": q})
        
        # Outils
        try: tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except: tools = None
        
        model = genai.GenerativeModel("gemini-2.5-flash", 
            system_instruction="Tu es un expert musical pédagogue. Vulgarise les concepts, sois cool, utilise des émojis. Guide pas à pas avec le manuel.",
            tools=tools)
        
        req = [q]
        if "pdf_ref" in st.session_state: req.append(st.session_state.pdf_ref)
        if "audio_gemini_ref" in st.session_state: req.append(st.session_state.audio_gemini_ref); req.append("Analyse l'audio.")
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                resp = model.generate_content(req)
                st.markdown(resp.text)
                st.session_state.chat_history.append({"role": "assistant", "content": resp.text})