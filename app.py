import streamlit as st
import google.generativeai as genai
import os
import tempfile
import yt_dlp
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Groovebox Tutor AI", page_icon="🎛️", layout="wide")

st.title("🎛️ Groovebox Tutor : Ton prof de musique perso")
st.markdown("""
1. Uploade le **manuel (PDF)** de ta machine.
2. Ajoute un **lien YouTube** (le tutoriel ou le son à copier).
3. L'IA t'explique comment faire !
""")

# --- FONCTIONS UTILITAIRES ---

def download_audio_from_url(url):
    """Télécharge l'audio sans conversion (pour éviter besoin de FFmpeg)"""
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

        with st.spinner("Téléchargement de l'audio YouTube..."):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                ext = info['ext']
                video_id = info['id']
                filename = f"{video_id}.{ext}"
                
                if os.path.exists(filename):
                    return filename, info.get('title', 'Audio Web')
                else:
                    return None, None
                    
    except Exception as e:
        st.error(f"Erreur téléchargement : {e}")
        return None, None

def get_mime_type(filename):
    if filename.endswith('.mp3'): return 'audio/mp3'
    if filename.endswith('.wav'): return 'audio/wav'
    if filename.endswith('.m4a'): return 'audio/mp4'
    if filename.endswith('.webm'): return 'audio/webm'
    return 'audio/mp3'

def upload_to_gemini(path, mime_type):
    """Envoie le fichier local à Gemini"""
    try:
        with st.spinner(f"Envoi du fichier à l'IA (Google)..."):
            file_ref = genai.upload_file(path=path, mime_type=mime_type)
            # Attente active du traitement
            while file_ref.state.name == "PROCESSING":
                time.sleep(1)
                file_ref = genai.get_file(file_ref.name)
            
            if file_ref.state.name == "FAILED":
                st.error("Le traitement du fichier par Google a échoué.")
                return None
                
            return file_ref
    except Exception as e:
        st.error(f"Erreur d'upload API : {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Configuration")
    api_key = st.text_input("Clé API Google AI Studio", type="password")
    
    st.header("2. Manuel")
    uploaded_pdf = st.file_uploader("Manuel (PDF)", type=["pdf"])

    st.header("3. Source Audio")
    tab1, tab2 = st.tabs(["🔗 Lien Web", "📁 Fichier"])
    
    # Gestion Lien Web
    with tab1:
        url_input = st.text_input("Lien YouTube / SoundCloud")
        if st.button("Charger le lien"):
            if url_input:
                file_path, title = download_audio_from_url(url_input)
                if file_path:
                    st.session_state.current_audio_path = file_path
                    st.session_state.current_audio_name = title
                    if "audio_gemini_ref" in st.session_state:
                        del st.session_state.audio_gemini_ref

    # Gestion Upload Fichier Local
    with tab2:
        uploaded_audio = st.file_uploader("Upload MP3/WAV/M4A", type=["mp3", "wav", "m4a"])
        if uploaded_audio:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                if "audio_gemini_ref" in st.session_state:
                     del st.session_state.audio_gemini_ref

    if st.button("🗑️ Reset Chat", type="primary"):
        st.session_state.chat_history = []
        if "audio_gemini_ref" in st.session_state: del st.session_state.audio_gemini_ref
        if "pdf_ref" in st.session_state: del st.session_state.pdf_ref
        st.rerun()

# --- LOGIQUE PRINCIPALE ---
if api_key:
    genai.configure(api_key=api_key)

    # A. Traitement du PDF
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(uploaded_pdf.getvalue())
            pdf_path = tmp_pdf.name
        ref = upload_to_gemini(pdf_path, "application/pdf")
        if ref:
            st.session_state.pdf_ref = ref
            st.success("📚 Manuel assimilé !")

    # B. Traitement de l'Audio
    if "current_audio_path" in st.session_state:
        file_path = st.session_state.current_audio_path
        
        try:
            st.info(f"🎵 Audio chargé : **{st.session_state.current_audio_name}**")
            st.audio(file_path)
        except:
            pass

        if "audio_gemini_ref" not in st.session_state:
            real_mime = get_mime_type(file_path)
            ref = upload_to_gemini(file_path, real_mime)
            if ref:
                st.session_state.audio_gemini_ref = ref

    # C. Chat Interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query := st.chat_input("Pose ta question..."):
        
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        # --- NOUVEAU PROMPT PÉDAGOGIQUE ---
        system_instruction = """
        Tu es un mentor musical passionné et pédagogue, expert en Grooveboxes (Elektron, Roland, Korg, etc.).
        Ta mission n'est pas de lire le manuel à la place de l'utilisateur, mais de lui apprendre à *comprendre* sa machine.

        RÈGLES D'OR DE TES RÉPONSES :
        1. 🧠 **Vulgarise d'abord** : Avant de donner une valeur technique, explique l'intention musicale avec des mots simples (ex: "Pour donner du punch au kick..." au lieu de "Règle l'enveloppe d'amplitude...").
        2. 🍎 **Utilise des analogies** : Compare les filtres à des tamis, les LFO à des mains invisibles qui tournent les boutons, etc.
        3. 📖 **Guide, ne dicte pas** : Utilise le PDF pour trouver les boutons exacts, mais ne noie pas l'utilisateur sous 50 réglages d'un coup. Concentre-toi sur les 3-4 réglages clés qui font 80% du son.
        4. ✨ **Style** : Sois encourageant, utilise des émojis pour aérer le texte, et structure ta réponse avec des titres clairs.

        STRUCTURE DE TA RÉPONSE :
        - **Analyse rapide** : "J'entends une basse très sourde avec un peu de saturation..."
        - **La Recette Magique** : Les 3 étapes clés pour y arriver (ex: 1. La Source, 2. Le Filtre, 3. L'Effet).
        - **Pas à pas** : Les manips précises du manuel pour réaliser ces étapes.
        """

        # --- CORRECTION FINALE ET ROBUSTE POUR GOOGLE SEARCH ---
        # On utilise les objets 'protos' directement pour éviter l'erreur de parsing du dictionnaire
        try:
            # Essai méthode Gemini 2.5 (Google Search)
            search_tool = genai.protos.Tool(
                google_search=genai.protos.GoogleSearch()
            )
        except:
            # Fallback (au cas où la version change encore)
            search_tool = None
            
        tools_list = [search_tool] if search_tool else None

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", 
            system_instruction=system_instruction,
            tools=tools_list
        )
        # --------------------------------------------------------

        request_content = [user_query]
        
        if "pdf_ref" in st.session_state and st.session_state.pdf_ref:
            request_content.append(st.session_state.pdf_ref)
            
        if "audio_gemini_ref" in st.session_state and st.session_state.audio_gemini_ref:
            request_content.append(st.session_state.audio_gemini_ref)
            request_content.append("Analyse cet audio.")

        with st.chat_message("assistant"):
            with st.spinner("Analyse en cours (Doc + Audio + Web)..."):
                try:
                    response = model.generate_content(request_content)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Une erreur est survenue : {e}")

else:
    st.warning("👈 Entre ta clé API pour commencer.")