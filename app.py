import streamlit as st
import google.generativeai as genai
import os
import tempfile
import time
import pathlib

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Groovebox Tutor",
    page_icon="🎹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLE (Design Pro) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
    .stButton > button {border-radius: 8px; font-weight: 600; border: none; transition: 0.2s;}
    
    /* Boutons Suggestions */
    button[kind="secondary"] {
        background-color: #21262d; color: #58a6ff; 
        border: 1px solid #30363d; border-radius: 20px; font-size: 0.85rem;
    }
    button[kind="secondary"]:hover {border-color: #58a6ff; background-color: #30363d;}
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    
    /* Zone de Drop */
    div[data-testid="stFileUploader"] {
        border: 1px dashed #30363d; border-radius: 10px; padding: 20px; background-color: #0d1117;
    }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS ---
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
    
    # 1. Input Clé API
    api_key = st.text_input("Clé API Google", type="password")
    
    # 2. Aide pour la clé (Expander)
    with st.expander("ℹ️ Comment avoir une clé gratuite ?"):
        st.markdown("""
        1. Va sur [Google AI Studio](https://aistudio.google.com/).
        2. Connecte-toi (Compte Google).
        3. Clique sur **"Get API key"**.
        4. Copie la clé et colle-la ici.
        *C'est 100% gratuit pour l'usage personnel.*
        """)
    
    st.markdown("---")
    
    # 3. Documentation
    st.info("📂 **Documentation**")
    uploaded_pdf = st.file_uploader("Manuel (PDF)", type=["pdf"], label_visibility="collapsed")
    
    st.markdown("---")
    
    # 4. Reset & Donation
    col_reset, col_don = st.columns(2)
    with col_reset:
        if st.button("🗑️ Reset", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    st.markdown("### ❤️ Soutenir le projet")
    st.markdown("Si cet outil t'aide à créer, tu peux soutenir le serveur !")
    # Remplace le lien ci-dessous par ton lien PayPal, BuyMeACoffee ou Tipeee
    st.link_button("☕ M'offrir un café", "https://www.buymeacoffee.com/", use_container_width=True)

# --- MAIN ---
col1, col2 = st.columns([5, 1])
with col1:
    st.title("Groovebox Tutor AI")
    # NOUVELLE ACCROCHE PLUS OUVERTE
    st.caption("Décrypte le son. Maîtrise ta machine. Crée ton propre grain.")

# --- ZONE AUDIO ---
with st.container(border=True):
    st.subheader("🎧 Source Audio")
    st.markdown("Importe un fichier audio (MP3, WAV, M4A) pour l'analyser.")
    
    uploaded_audio = st.file_uploader("Glisse ton fichier ici", type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    
    if uploaded_audio:
        if "current_audio_name" not in st.session_state or st.session_state.current_audio_name != uploaded_audio.name:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                st.rerun()

    if "current_audio_path" in st.session_state:
        st.success(f"🎵 Piste active : **{st.session_state.get('current_audio_name', 'Inconnu')}**")
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

    # Phrases ajustées pour être moins "copie-colle"
    if has_audio and has_pdf:
        suggestions.append("🔥 Décrypte ce son et dis-moi comment l'approcher")
    if has_audio:
        suggestions.append("🥁 Analyse le groove et la texture")
    if has_pdf:
        suggestions.append("🎛️ Explique-moi une fonction créative du manuel")
    if not suggestions:
        suggestions.append("🔍 Trouve une astuce de Sound Design")

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
        Tu es un expert musical pédagogue et inspirant.
        CAPACITÉ CRITIQUE : Tu as reçu un fichier audio. TU DOIS L'ÉCOUTER.
        Ne dis jamais que tu ne peux pas. Analyse le spectre, le timbre et le rythme.
        
        Ta mission : 
        1. Analyse le son (texture, technique, émotion).
        2. Fais le lien avec le manuel PDF pour proposer des techniques de création.
        3. Ne te limite pas à la copie : propose des variations, explique le "pourquoi" technique.
        4. Sois concis, utilise des émojis et reste encourageant.
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