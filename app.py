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
    
    /* Boutons standards */
    .stButton > button {border-radius: 8px; font-weight: 600; border: none; transition: 0.2s;}
    
    /* Bouton vert (Charger lien) */
    div[data-testid="stHorizontalBlock"] > div:first-child button {background-color: #238636; color: white;}
    
    /* Boutons de Suggestion (Chips) */
    button[kind="secondary"] {
        background-color: #21262d; 
        color: #58a6ff; 
        border: 1px solid #30363d;
        border-radius: 20px; /* Arrondi style 'Pill' */
        font-size: 0.85rem;
    }
    button[kind="secondary"]:hover {
        border-color: #58a6ff;
        background-color: #30363d;
    }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS ---
def download_audio_from_url(url):
    try:
        ydl_opts = {'format': 'bestaudio[ext=m4a]/best', 'outtmpl': '%(id)s.%(ext)s', 'noplaylist': True, 'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"{info['id']}.{info['ext']}"
            if os.path.exists(filename): return filename, info.get('title', 'Audio Web')
            return None, None
    except: return None, None

def get_mime_type(filename):
    if filename.endswith('.m4a'): return 'audio/mp4'
    if filename.endswith('.wav'): return 'audio/wav'
    if filename.endswith('.mp3'): return 'audio/mp3'
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
                with st.status("Téléchargement...", expanded=True) as status:
                    f, t = download_audio_from_url(url_input)
                    if f:
                        st.session_state.current_audio_path = f
                        st.session_state.current_audio_name = t
                        status.update(label="✅ Prêt !", state="complete", expanded=False)
    
    with c2:
        uploaded_audio = st.file_uploader("Fichier Local", type=["mp3", "wav", "m4a"])
        if uploaded_audio:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name

    if "current_audio_path" in st.session_state:
        st.audio(st.session_state.current_audio_path)
        st.caption(f"Piste active : {st.session_state.get('current_audio_name', 'Inconnu')}")

# --- LOGIC INITIALIZATION ---
if api_key:
    genai.configure(api_key=api_key)
    
    # PDF Load
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.spinner("Lecture du manuel..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_pdf_to_gemini(p)
            if r: st.session_state.pdf_ref = r; st.toast("Manuel chargé !", icon="📘")

    # --- HISTORIQUE DU CHAT ---
    st.divider()
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # --- SUGGESTIONS INTELLIGENTES (UX) ---
    # On définit les suggestions selon le contexte
    suggestions = []
    
    # 1. Contexte Audio
    if "current_audio_path" in st.session_state:
        suggestions.append("🎹 Comment refaire ce son exactement ?")
        suggestions.append("🥁 Analyse le rythme de cet audio")
    
    # 2. Contexte PDF
    if "pdf_ref" in st.session_state:
        suggestions.append("🎛️ Explique-moi le filtre (Page Manual)")
        suggestions.append("💾 Comment on sauvegarde un projet ?")
    
    # 3. Contexte Général (Web)
    if not suggestions: # Si rien n'est chargé
        suggestions.append("🔍 Trouve un tuto 'Techno Rumble'")
        suggestions.append("🔊 C'est quoi la différence entre Gain et Volume ?")

    # Affichage des bulles
    if suggestions:
        st.markdown("<small style='color: #8b949e; margin-bottom: 5px;'>💡 Suggestions rapides :</small>", unsafe_allow_html=True)
        cols = st.columns(len(suggestions))
        choice = None
        for i, col in enumerate(cols):
            if col.button(suggestions[i], key=f"sugg_{i}", type="secondary", use_container_width=True):
                choice = suggestions[i]

    # --- GESTION DE L'INPUT (Texte OU Bouton) ---
    prompt = st.chat_input("Pose ta question ici...")

    # Si on a cliqué sur un bouton, on force le prompt
    if choice:
        prompt = choice
    
    if prompt:
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Tools
        try: tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except: tools = None
        
        # System Prompt
        sys_prompt = """
        Tu es un expert musical pédagogue.
        CAPACITÉ CRITIQUE : Tu as reçu un fichier audio dans cette requête. TU DOIS L'ÉCOUTER.
        Ne dis jamais que tu ne peux pas. Analyse le spectre, le timbre et le rythme.
        
        Ta mission :
        1. Analyse le son fourni.
        2. Donne la recette pour le refaire avec la machine du manuel PDF.
        3. Sois cool, utilise des émojis et vulgarise.
        """
        
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=sys_prompt, tools=tools)
        
        req = [prompt]
        if "pdf_ref" in st.session_state: req.append(st.session_state.pdf_ref)
        
        # AUDIO INLINE (Crucial pour éviter les hallucinations)
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