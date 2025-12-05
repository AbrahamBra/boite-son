import streamlit as st
import google.generativeai as genai
import os
import tempfile
import yt_dlp
import time
import pathlib

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="🎹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
    .stButton > button {border-radius: 8px; font-weight: 600; border: none; transition: 0.2s;}
    div[data-testid="stHorizontalBlock"] > div:first-child button {background-color: #238636; color: white;}
    
    button[kind="secondary"] {
        background-color: #21262d; color: #58a6ff; 
        border: 1px solid #30363d; border-radius: 20px; font-size: 0.85rem;
    }
    button[kind="secondary"]:hover {border-color: #58a6ff; background-color: #30363d;}
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

# --- FONCTION TÉLÉCHARGEMENT BLINDÉE (ANTI-403) ---
def download_audio_from_url(url):
    try:
        # Options pour contourner les blocages basiques
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/best',
            'outtmpl': '%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            # On se fait passer pour un navigateur Windows standard
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'referer': 'https://www.google.com/',
            'nocheckcertificate': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"{info['id']}.{info['ext']}"
            if os.path.exists(filename): 
                return filename, info.get('title', 'Audio Web')
            return None, None
            
    except Exception as e:
        # On renvoie l'erreur pour l'afficher à l'utilisateur
        print(f"Erreur Download: {e}") 
        return None, str(e)

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
                with st.status("Tentative de connexion à YouTube...", expanded=True) as status:
                    f, t_or_error = download_audio_from_url(url_input)
                    
                    if f:
                        # Succès
                        st.session_state.current_audio_path = f
                        st.session_state.current_audio_name = t_or_error
                        status.update(label="✅ Audio récupéré !", state="complete")
                        time.sleep(1)
                        st.rerun()
                    else:
                        # Échec (Erreur 403 probable)
                        status.update(label="❌ Échec du téléchargement", state="error")
                        st.error(f"YouTube a bloqué la connexion (Erreur 403). C'est fréquent sur les serveurs cloud.")
                        st.info("💡 **Solution :** Télécharge le MP3 toi-même (via un site comme y2mate) et glisse-le dans la case 'Fichier Local' à droite ->")

    with c2:
        uploaded_audio = st.file_uploader("Fichier Local", type=["mp3", "wav", "m4a"])
        if uploaded_audio:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                st.rerun()

    # LECTEUR AUDIO
    if "current_audio_path" in st.session_state:
        st.success(f"🎵 Piste chargée : **{st.session_state.get('current_audio_name', 'Inconnu')}**")
        st.audio(st.session_state.current_audio_path)

# --- LOGIC INITIALIZATION ---
if api_key:
    genai.configure(api_key=api_key)
    
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.spinner("Lecture du manuel..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_pdf_to_gemini(p)
            if r: st.session_state.pdf_ref = r; st.toast("Manuel chargé !", icon="📘")

    # --- CHAT ---
    st.divider()
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # --- SUGGESTIONS (UX) ---
    suggestions = []
    has_audio = "current_audio_path" in st.session_state
    has_pdf = "pdf_ref" in st.session_state

    if has_audio and has_pdf:
        suggestions.append("🔥 Dis-moi comment refaire ce son avec ma machine")
    if has_audio:
        suggestions.append("🥁 Analyse le rythme et le swing")
    if has_pdf:
        suggestions.append("🎛️ À quoi sert le bouton [FUNC] ?")
    if not suggestions:
        suggestions.append("🔍 Trouve un tuto pour débutant")

    if suggestions:
        st.markdown("<small style='color: #8b949e; margin-bottom: 5px;'>💡 Idées :</small>", unsafe_allow_html=True)
        cols = st.columns(min(len(suggestions), 3)) 
        choice = None
        for i, col in enumerate(cols):
            if i < 3:
                if col.button(suggestions[i], key=f"sugg_{i}", type="secondary", use_container_width=True):
                    choice = suggestions[i]

    # --- INPUT ---
    prompt = st.chat_input("Pose ta question ici...")
    if choice: prompt = choice
    
    if prompt:
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        try: tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except: tools = None
        
        sys_prompt = """
        Tu es un expert musical pédagogue.
        CAPACITÉ CRITIQUE : Tu as reçu un fichier audio. TU DOIS L'ÉCOUTER.
        Ne dis jamais que tu ne peux pas. Analyse le spectre, le timbre et le rythme.
        Ta mission : Analyse le son, Donne la recette PDF, Sois cool.
        """
        
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=sys_prompt, tools=tools)
        
        req = [prompt]
        if "pdf_ref" in st.session_state: req.append(st.session_state.pdf_ref)
        
        if "current_audio_path" in st.session_state:
            audio_path = st.session_state.current_audio_path
            mime = get_mime_type(audio_path)
            audio_data = pathlib.Path(audio_path).read_bytes()
            req.append({"mime_type": mime, "data": audio_data})
            req.append("⚠️ Analyse impérativement les données audio ci-dessus.")

        with st.chat_message("assistant"):
            with st.spinner("Analyse en cours..."):
                try:
                    resp = model.generate_content(req)
                    st.markdown(resp.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
                except Exception as e:
                    st.error(f"Erreur : {e}")