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
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container {padding-top: 3rem; padding-bottom: 5rem;}
    
    /* Info Box */
    div[data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.05); border: 1px solid #303030; color: #E0E0E0; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DICTIONNAIRE COMPLET ---
TR = {
    "Français 🇫🇷": {
        "settings": "1. Configuration",
        "api_label": "Clé API Google",
        "api_help": "ℹ️ Pourquoi une clé perso ?",
        "api_desc": "Projet open-source. L'usage de votre propre clé gratuite garantit votre indépendance et la gratuité totale de l'outil.",
        "doc_section": "2. Votre Machine",
        "doc_help": "🔍 Trouver mon manuel officiel",
        "manual_upload": "Déposer le Manuel PDF ici",
        "audio_title": "🎧 Le Son à Analyser",
        "audio_subtitle": "C'est ici que la magie opère. Glissez un fichier pour lancer l'écoute.",
        "audio_label": "Fichier Audio",
        "style_section": "3. Style Pédagogique",
        "memory_title": "4. 💾 Session & Mémoire",
        "memory_help": "💡 Comment ça marche ?",
        "memory_desc": "**Sauvegarder votre progression :**\n\n1. En fin de session, cliquez sur **💾 Télécharger** en bas\n2. Un fichier .txt sera téléchargé avec tout l'historique\n3. La prochaine fois, glissez ce fichier ici pour reprendre\n\nL'IA se souviendra de tout le contexte !",
        "memory_load": "📂 Reprendre une session précédente",
        "memory_save": "💾 Télécharger Session",
        "reset": "🔄 Nouvelle Session",
        "about": "📖 Philosophie du projet",
        "about_text": """**Groovebox Tutor** est né d'une frustration : celle de voir des musiciens acheter des machines incroyables... pour finalement copier des presets trouvés sur Reddit.

### Notre vision

Nous croyons que **comprendre** vaut mieux que **copier**. Que la vraie créativité vient de la maîtrise technique. Que chaque machine mérite qu'on apprenne à lui parler.

### Comment ça marche

L'IA agit comme votre **binôme de studio** :
- 🎧 Elle écoute votre référence sonore
- 📖 Elle lit le manuel de votre machine
- 🎛️ Elle vous guide pour **recréer** le son par vous-même

Pas de preset tout fait. Pas de solution miracle. Juste de la **pédagogie**, étape par étape.

### Pourquoi c'est gratuit ?

Parce que la connaissance doit être accessible. Ce projet est open-source et le restera. Si vous progressez grâce à lui, un café virtuel fait toujours plaisir ☕

*Fait avec ❤️ pour les beatmakers, les sound designers, et tous ceux qui refusent de rester en surface.*""",
        "support": "☕ Soutenir (Don)",
        "title": "Groovebox Tutor",
        "subtitle": "Votre binôme technique. Décryptez le son. Maîtrisez votre machine.",
        "placeholder": "Posez une question technique sur ce son...",
        "onboarding": "👋 **Objectif : Autonomie**\n\n1. Importez le **Manuel** de votre instrument (à gauche)\n2. Proposez un **Son** qui vous inspire (ci-dessous)\n3. Votre binôme analyse la texture et vous enseigne **les étapes techniques** pour recréer ce grain vous-même",
        "legal": "⚠️ Outil d'analyse à but éducatif. L'inspiration est légale, le plagiat ne l'est pas.",
        "sugg_1": "Analyse ce son",
        "sugg_2": "Structure rythmique",
        "sugg_3": "Fonction cachée",
        "style_label": "Approche Pédagogique",
        "tones": ["🤙 Mentor Cool", "👔 Expert Technique", "⚡ Synthétique"],
        "formats": ["📝 Cours Complet", "✅ Checklist", "💬 Interactif"],
        "manual_loaded": "✅ Manuel assimilé",
        "active_track": "Piste active :",
        "session_reloaded": "✅ Session rechargée ! L'IA se souvient du contexte."
    },
    "English 🇬🇧": {
        "settings": "1. Setup",
        "api_label": "Google API Key",
        "api_help": "ℹ️ Why a personal key?",
        "api_desc": "Open-source project. Using your own free key ensures your independence and total tool freedom.",
        "doc_section": "2. Your Gear",
        "doc_help": "🔍 Find official manual",
        "manual_upload": "Drop PDF Manual here",
        "audio_title": "🎧 The Sound",
        "audio_subtitle": "Magic happens here. Drop your audio file.",
        "audio_label": "Audio File",
        "style_section": "3. Teaching Style",
        "memory_title": "4. 💾 Session & Memory",
        "memory_help": "💡 How does it work?",
        "memory_desc": "**Save your progress:**\n\n1. At the end of your session, click **💾 Download** below\n2. A .txt file will be downloaded with all the history\n3. Next time, drop that file here to resume\n\nThe AI will remember all context!",
        "memory_load": "📂 Resume previous session",
        "memory_save": "💾 Download Session",
        "reset": "🔄 New Session",
        "about": "📖 Project Philosophy",
        "about_text": """**Groovebox Tutor** was born from frustration: watching musicians buy incredible machines... only to copy presets from Reddit.

### Our vision

We believe **understanding** beats **copying**. That real creativity comes from technical mastery. That every machine deserves to be learned properly.

### How it works

The AI acts as your **studio partner**:
- 🎧 It listens to your reference sound
- 📖 It reads your machine's manual
- 🎛️ It guides you to **recreate** the sound yourself

No ready-made presets. No magic solution. Just **pedagogy**, step by step.

### Why is it free?

Because knowledge should be accessible. This project is open-source and will stay that way. If you progress thanks to it, a virtual coffee is always appreciated ☕

*Made with ❤️ for beatmakers, sound designers, and everyone who refuses to stay on the surface.*""",
        "support": "☕ Donate",
        "title": "Groovebox Tutor",
        "subtitle": "Your technical partner. Decode sound. Master your gear.",
        "placeholder": "Ask a technical question about this sound...",
        "onboarding": "👋 **Goal: Autonomy**\n\n1. Upload your instrument's **Manual** (left sidebar)\n2. Provide a **Sound** that inspires you (below)\n3. Your partner analyzes the texture and teaches you **the technical steps** to recreate it yourself",
        "legal": "⚠️ Educational analysis tool. Inspiration is legal, plagiarism is not.",
        "sugg_1": "Analyze sound",
        "sugg_2": "Rhythm structure",
        "sugg_3": "Hidden feature",
        "style_label": "Teaching Approach",
        "tones": ["🤙 Cool Mentor", "👔 Technical Expert", "⚡ Direct"],
        "formats": ["📝 Full Lesson", "✅ Checklist", "💬 Interactive"],
        "manual_loaded": "✅ Manual loaded",
        "active_track": "Active track:",
        "session_reloaded": "✅ Session reloaded! The AI remembers the context."
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

# --- CONSTRUCTION DU PROMPT AVEC STYLES ---
def build_system_prompt(lang, style_tone, style_format, memory_context, has_manual):
    
    # Mapping des tons
    TONE_PROFILES = {
        "🤙 Mentor Cool": {
            "voice": "Ton décontracté, tutoiement, encourage l'expérimentation",
            "examples": "Utilise des analogies fun",
            "energy": "Enthousiaste 🎛️"
        },
        "👔 Expert Technique": {
            "voice": "Ton professionnel mais accessible, précis",
            "examples": "Vocabulaire exact du fabricant",
            "energy": "Rigoureux mais pédagogue"
        },
        "⚡ Synthétique": {
            "voice": "Direct, efficace",
            "examples": "Infos essentielles",
            "energy": "Minimaliste"
        },
        "🤙 Cool Mentor": {
            "voice": "Casual, encouraging",
            "examples": "Fun analogies",
            "energy": "Enthusiastic 🎛️"
        },
        "👔 Technical Expert": {
            "voice": "Professional, precise",
            "examples": "Manufacturer vocabulary",
            "energy": "Rigorous but pedagogical"
        },
        "⚡ Direct": {
            "voice": "Straight to the point",
            "examples": "Essential info",
            "energy": "Minimalist"
        }
    }
    
    # Mapping des formats
    FORMAT_PROFILES = {
        "📝 Cours Complet": "Explications détaillées, structure claire",
        "✅ Checklist": "Étapes concrètes, listes numérotées",
        "💬 Interactif": "Dialogue naturel, accessible",
        "📝 Full Lesson": "Detailed explanations, clear structure",
        "✅ Checklist": "Concrete steps, numbered lists",
        "💬 Interactive": "Natural dialogue, accessible"
    }
    
    tone_profile = TONE_PROFILES.get(style_tone, TONE_PROFILES.get("🤙 Mentor Cool", TONE_PROFILES.get("🤙 Cool Mentor")))
    format_profile = FORMAT_PROFILES.get(style_format, FORMAT_PROFILES.get("📝 Cours Complet", FORMAT_PROFILES.get("📝 Full Lesson")))
    
    return f"""
# TU ES
**Groovebox Tutor** - Assistant technique pour groovebox et synthétiseurs.

# TA MISSION
Aider l'utilisateur à **maîtriser sa machine** et **composer les sons qu'il veut**.

Tu n'es PAS un prof qui pose des questions.  
Tu es un **binôme technique** qui donne des réponses claires.

---

# 🎨 TON STYLE

**Ton** : {tone_profile['voice']}  
**Format** : {format_profile}  
**Langue** : {lang.split()[0]}

{memory_context}

---

# 📖 RESSOURCES DISPONIBLES

{"✅ **MANUEL FOURNI** : Utilise-le comme référence. Cite les pages/sections." if has_manual else "⚠️ **PAS DE MANUEL** : Explique les concepts généraux de synthèse."}

---

# 🎯 COMMENT RÉPONDRE

## Si l'utilisateur pose une question SANS fichier audio :

**Exemple** : "Comment faire un kick puissant ?"

→ Réponds directement :
1. Explique les étapes (claires, numérotées)
2. Donne des fourchettes de valeurs ("cutoff entre 30-50%")
3. Explique pourquoi ça marche
4. {"Cite le manuel (page/section)" if has_manual else "Reste sur les principes universels"}

**NE DEMANDE PAS** de fichier audio.  
**NE POSE PAS** de questions comme "Qu'en penses-tu ?"

---

## Si l'utilisateur partage un fichier audio :

1. **Analyse-le** :
   - Fréquences (sub/bass/mid/high)
   - Envelope (ADSR)
   - Effets (reverb, delay, etc.)

2. **Explique comment le recréer** :
   - Étapes concrètes
   - Fourchettes de valeurs
   - {"Références au manuel" if has_manual else "Principes généraux"}

---

# ❌ NE FAIS JAMAIS

- Poser des questions socratiques ("Qu'entends-tu ?", "Qu'en penses-tu ?")
- Demander à l'utilisateur de partager un son s'il n'en a pas partagé
- Donner des valeurs exactes (ex: "Cutoff = 63")
- Fournir un preset clé-en-main

---

# ✅ FAIS TOUJOURS

- Répondre directement à la question
- Expliquer le "pourquoi" technique
- Donner des étapes claires
- Rester actionnable
- {"Citer le manuel quand pertinent" if has_manual else "Expliquer les concepts généraux"}

---

# 🔧 TES CONNAISSANCES

- **Synthèse** : soustractive, FM, wavetable, granulaire, sampling
- **Machines** : Elektron, MPC, SP-404, OP-1, Volca, etc.
- **Signal** : filtres, ADSR, LFO, modulation
- **Effets** : reverb, delay, distortion, chorus, etc.

---

# ⚖️ ÉTHIQUE

Cet outil est **éducatif**.  
Objectif = **Apprendre les techniques**, pas copier des presets commerciaux.

---

Prêt à t'aider ! 🎛️
"""
# IDENTITÉ
Tu es **Groovebox Tutor**, expert en sound design et pédagogue musical.

# MISSION
Analyser l'audio fourni, {"utiliser le manuel technique de la machine" if has_manual else "expliquer les concepts généraux de synthèse"}, et enseigner à l'utilisateur comment recréer le son de manière autonome.

---

# 🎨 STYLE DE COMMUNICATION

## Ton ({style_tone})
{tone_profile['voice']}
{tone_profile['examples']}
{tone_profile['energy']}

## Format de réponse ({style_format})
{format_profile}

## Langue
{lang.split()[0]} - Adapte tout ton vocabulaire et tes exemples culturels à cette langue.

{memory_context}

---

# 🎧 ANALYSE AUDIO (ce que tu fais en interne)

Quand l'utilisateur partage un son :

1. **Décomposition spectrale**
   - Fréquences dominantes (sub/bass/mid/high)
   - Harmoniques présents (fondamentale, octaves, partiels)
   - Composantes de bruit (white/pink noise, texture)

2. **Analyse temporelle**
   - Envelope globale : Attack / Decay / Sustain / Release
   - Modulations : vibrato, tremolo, filter sweep, pitch bend
   - Rythmique interne : gates, arpeggios, patterns

3. **Identification des effets**
   - Reverb (taille, decay, wet/dry)
   - Delay (time, feedback, ping-pong)
   - Distortion/saturation
   - Filtrage dynamique (LFO, envelope)
   - Autres (chorus, phaser, flanger, etc.)

4. **Hypothèse de synthèse**
   - Type probable : soustractive / FM / wavetable / sample-based / granular
   - Forme d'onde estimée
   - Chaîne de traitement (oscillator → filter → envelope → FX)

---

# 📖 UTILISATION DU MANUEL

{"✅ MANUEL FOURNI - Utilise-le comme référence absolue :" if has_manual else "⚠️ PAS DE MANUEL - Reste générique sur la synthèse :"}

{"**Tu dois :**" if has_manual else "**Tu dois :**"}
{'''
- Citer les sections/pages précises pour chaque concept
- Adapter ton vocabulaire aux termes exacts du fabricant
- Identifier les features spécifiques de cette machine
- Montrer OÙ trouver chaque paramètre dans l'interface
- Utiliser les noms de modes/algorithmes propres à cette machine

**Exemple :**
"Pour ce filtre, consulte page 42 section FILTER TYPE — le Digitakt utilise un filtre 2-pôles avec résonance variable. Tu le trouveras en appuyant sur [FUNC] + [TRIG]."
''' if has_manual else '''
- Expliquer les concepts universels de synthèse
- Donner des exemples applicables à la plupart des machines
- Rester sur les principes théoriques sans citer de pages
- Encourager l'utilisateur à chercher dans SON manuel si disponible

**Exemple :**
"Ce type de filtre passe-bas avec résonance est standard sur la plupart des grooveboxes. Cherche dans ton manuel les sections 'FILTER' ou 'SYNTH ENGINE'."
'''}

---

# 🎓 MÉTHODOLOGIE PÉDAGOGIQUE

## ❌ CE QUE TU NE FAIS JAMAIS
- Donner les valeurs exactes des paramètres (ex: "Cutoff = 63")
- Fournir un preset clé-en-main
- Juste décrire sans expliquer le "pourquoi"
- Copier-coller des passages du manuel (reformule toujours)

## ✅ CE QUE TU FAIS TOUJOURS
- Expliquer la LOGIQUE du son (relation cause-effet)
- Guider par des questions ouvertes {" surtout en mode 💬 Interactive" if "Interactive" in style_format or "Interactif" in style_format else ""}
- Proposer des expérimentations à faire
- Donner des fourchettes de valeurs ("entre 40% et 70%")
- Utiliser des analogies concrètes adaptées à la culture {lang.split()[0]}

---

# 📐 STRUCTURE DE RÉPONSE

{"### Format PROSE (Full Lesson)" if "Full Lesson" in style_format or "Cours Complet" in style_format else ""}
{"### Format CHECKLIST (actionnable)" if "Checklist" in style_format else ""}
{"### Format INTERACTIF (Socratique)" if "Interactive" in style_format or "Interactif" in style_format else ""}

{'''
**Étape 1 : Observation initiale**
Décris ce que tu entends (vocabulaire technique accessible).

**Étape 2 : Question ouverte**
Engage la réflexion de l'utilisateur.

**Étape 3 : Explication conceptuelle**
Explique les mécanismes en jeu avec références au manuel.

**Étape 4 : Guide d'expérimentation**
Donne des pistes sans donner la solution.

**Étape 5 : Check-in**
Invite au retour d'expérience.
''' if "Full Lesson" in style_format or "Cours Complet" in style_format else ""}

{'''
**Format : Liste d'actions concrètes**

✅ **ANALYSE** (ce que tu détectes)
✅ **CONCEPTS** (théorie express)
✅ **ACTIONS** (étapes à suivre)
✅ **CHECK** (validation)
''' if "Checklist" in style_format else ""}

{'''
**Format : Dialogue + Questions**

🔊 **Observation**
❓ **Question**
💡 **Explication**
🧪 **Expérimentation guidée**
🔄 **Itération**
''' if "Interactive" in style_format or "Interactif" in style_format else ""}

---

# 🧠 PRINCIPES PÉDAGOGIQUES

1. **Autonomie > Solution rapide**
   Goal = COMPRENDRE la synthèse, pas copier un preset.

2. **Apprentissage par l'erreur**
   Encourage les tests ratés : "Qu'as-tu appris ?"

3. **Analogies culturelles**
   Filtre = robinet, envelope = rebond de balle, résonance = corde qui vibre

4. **Progressivité**
   Layer 1 : Son de base → Layer 2 : Envelope → Layer 3 : Modulations → Layer 4 : Effets

5. **Contexte matériel**
   {"Adapte tout au gear de l'utilisateur détecté via le manuel" if has_manual else "Reste sur les principes universels applicables à toute machine"}

---

# ⚖️ CADRE LÉGAL & ÉTHIQUE

⚠️ **IMPORTANT** : Outil **éducatif**, pas un copieur de sons.

- **Inspiration légale** : Analyser les techniques ✅
- **Plagiat illégal** : Reproduire exactement un preset commercial ❌

Si le son source = preset protégé évident, rappelle :
"Je vais t'expliquer les TECHNIQUES utilisées, pas te donner une copie conforme. L'objectif est d'apprendre, pas de plagier."

---

# 🔧 CONNAISSANCES TECHNIQUES

Tu maîtrises :
- **Synthèse** : soustractive, FM, wavetable, granulaire, sampling
- **Grooveboxes** : Elektron (Digitakt/Digitone/Syntakt), MPC, SP-404, OP-1, etc.
- **Signal** : filtres (LP/HP/BP/notch), ADSR, LFO, mod matrix
- **Effets** : reverb, delay, distortion, chorus, phaser, compressor
- **Sound design** : layering, texture, mouvement, espace stéréo

---

Prêt à analyser ton premier son ! 🎧
"""
    
    return sys_prompt
# --- 5. INTERFACE ---

# --- SIDEBAR ---
with st.sidebar:
    lang = st.selectbox("Langue / Language", list(TR.keys()), label_visibility="collapsed")
    T = TR.get(lang, TR["Français 🇫🇷"])
    
    # 1. CONFIGURATION
    st.markdown(f"### {T['settings']}")
    api_key = st.text_input(T["api_label"], type="password", placeholder="AIzaSy...")
    with st.expander(T["api_help"]):
        st.caption(T["api_desc"])
        st.markdown("[Google AI Studio](https://aistudio.google.com/) (Free)")

    st.markdown("---")
    
    # 2. FICHIERS (tout regroupé)
    st.markdown("### 2. 📁 Fichiers" if lang == "Français 🇫🇷" else "### 2. 📁 Files")
    
    # Helper pour trouver les manuels
    with st.expander(T["doc_help"]):
        MANUAL_LINKS = {
            "Elektron Digitakt II": "https://www.elektron.se/en/support-downloads/digitakt-ii",
            "Roland SP-404 MKII": "https://www.roland.com/global/products/sp-404mk2/support/",
            "TE EP-133 K.O. II": "https://teenage.engineering/downloads/ep-133",
            "Korg Volca Sample 2": "https://www.korg.com/us/support/download/product/0/867/",
            "Akai MPC One/Live": "https://www.akaipro.com/mpc-one",
            "Novation Circuit Tracks": "https://downloads.novationmusic.com/novation/circuit/circuit-tracks",
            "Arturia MicroFreak": "https://www.arturia.com/products/hardware-synths/microfreak/resources"
        }
        machine = st.selectbox("Machine", list(MANUAL_LINKS.keys()), label_visibility="collapsed")
        st.link_button(f"⬇️ {machine}", MANUAL_LINKS[machine], use_container_width=True)
    
    # Upload 1 : Manuel PDF
    st.caption("📄 Manuel de votre machine" if lang == "Français 🇫🇷" else "📄 Your gear manual")
    uploaded_pdf = st.file_uploader(
        "Manuel PDF", 
        type=["pdf"], 
        label_visibility="collapsed",
        key="pdf_upload"
    )
    if uploaded_pdf:
        st.success(T["manual_loaded"])
    
    # Upload 2 : Son à analyser
    st.caption("🎵 Son à analyser" if lang == "Français 🇫🇷" else "🎵 Sound to analyze")
    uploaded_audio = st.file_uploader(
        "Audio", 
        type=["mp3", "wav", "m4a"], 
        label_visibility="collapsed",
        key="audio_upload"
    )
    if uploaded_audio:
        if "current_audio_name" not in st.session_state or st.session_state.current_audio_name != uploaded_audio.name:
            suffix = f".{uploaded_audio.name.split('.')[-1]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_audio.getvalue())
                st.session_state.current_audio_path = tmp.name
                st.session_state.current_audio_name = uploaded_audio.name
                st.rerun()
    
    if "current_audio_name" in st.session_state:
        st.success(f"✅ {st.session_state.current_audio_name}")
        st.audio(st.session_state.current_audio_path)
    
    # Upload 3 : Session précédente
    with st.expander("💾 " + ("Reprendre une session" if lang == "Français 🇫🇷" else "Resume session")):
        st.caption(T["memory_desc"])
        uploaded_memory = st.file_uploader(
            "Session .txt", 
            type=["txt"], 
            label_visibility="collapsed",
            key="mem_upload"
        )
        if uploaded_memory:
            st.session_state.memory_content = uploaded_memory.getvalue().decode("utf-8")
            st.success(T["session_reloaded"])

    st.markdown("---")
    
    # 3. STYLE PÉDAGOGIQUE
    st.markdown(f"### {T['style_section']}")
    style_tone = st.selectbox("Ton", T["tones"], index=0, label_visibility="collapsed")
    style_format = st.radio("Format", T["formats"], index=0, label_visibility="collapsed")

    st.markdown("---")
    
    # FOOTER : ACTIONS (seulement si une conversation existe)
    if "chat_history" in st.session_state and st.session_state.chat_history:
        history_txt = format_history(st.session_state.chat_history)
        
        col_dl, col_reset = st.columns(2)
        
        with col_dl:
            st.download_button(
                "💾",
                history_txt, 
                f"groovebox_session_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", 
                "text/plain", 
                use_container_width=True,
                type="primary",
                help=T["memory_save"]
            )
        
        with col_reset:
            if st.button(
                "🔄",
                use_container_width=True,
                type="secondary",
                help=T["reset"]
            ):
                st.session_state.clear()
                st.rerun()
    
    # Footer philosophie (toujours visible)
    with st.expander(T["about"]):
        st.markdown(T["about_text"])
        st.markdown(f"[{T['support']}](https://www.buymeacoffee.com/)")

# --- MAIN AREA ---
st.title(T["title"])
st.markdown(f"<h3 style='margin-top: -20px; margin-bottom: 40px; color: #808080;'>{T['subtitle']}</h3>", unsafe_allow_html=True)

# Onboarding si pas de clé API
if not api_key:
    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, rgba(30,30,35,0.8) 0%, rgba(20,20,25,0.9) 100%);
        border-left: 3px solid #888;
        padding: 2rem;
        border-radius: 8px;
        margin: 2rem 0;
    '>
        <h3 style='color: #FFF; margin-top: 0; font-weight: 300; letter-spacing: 0.5px;'>
            👋 {'Objectif : Autonomie' if lang == 'Français 🇫🇷' else 'Goal: Autonomy'}
        </h3>
        <ol style='color: #CCC; line-height: 1.8; font-size: 1.05rem;'>
            <li>{'Importez le <strong>Manuel</strong> de votre instrument (à gauche)' if lang == 'Français 🇫🇷' else 'Upload your instrument\'s <strong>Manual</strong> (left sidebar)'}</li>
            <li>{'Proposez un <strong>Son</strong> qui vous inspire (à gauche aussi)' if lang == 'Français 🇫🇷' else 'Provide a <strong>Sound</strong> that inspires you (left sidebar)'}</li>
            <li>{'Votre binôme analyse la texture et vous enseigne les <strong>étapes techniques</strong> pour recréer ce grain vous-même' if lang == 'Français 🇫🇷' else 'Your partner analyzes the texture and teaches you <strong>the technical steps</strong>'}</li>
        </ol>
        <p style='color: #999; font-size: 0.9rem; margin-bottom: 0; margin-top: 1.5rem;'>
            ⚠️ {'Outil d\'analyse à but éducatif. L\'inspiration est légale, le plagiat ne l\'est pas.' if lang == 'Français 🇫🇷' else 'Educational analysis tool. Inspiration is legal, plagiarism is not.'}
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- LOGIC ---
if api_key:
    genai.configure(api_key=api_key)
    
    if uploaded_pdf and "pdf_ref" not in st.session_state:
        with st.status("Lecture du manuel..." if lang == "Français 🇫🇷" else "Reading manual...", expanded=False) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
                t.write(uploaded_pdf.getvalue())
                p = t.name
            r = upload_pdf_to_gemini(p)
            if r: 
                st.session_state.pdf_ref = r
                status.update(label=T["manual_loaded"], state="complete")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = None
    if not st.session_state.chat_history:
        col1, col2, col3 = st.columns(3)
        if col1.button(T["sugg_1"], type="secondary", use_container_width=True):
            prompt = T["sugg_1"]
        elif col2.button(T["sugg_2"], type="secondary", use_container_width=True):
            prompt = T["sugg_2"]
        elif col3.button(T["sugg_3"], type="secondary", use_container_width=True):
            prompt = T["sugg_3"]

    user_input = st.chat_input(T["placeholder"])
    if user_input:
        prompt = user_input

    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        try:
            tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except:
            tools = None
        
        memory_context = ""
        if "memory_content" in st.session_state:
            memory_context = f"## 🧠 CONTEXTE MÉMOIRE\n{st.session_state.memory_content}\n"

        sys_prompt = build_system_prompt(
            lang=lang,
            style_tone=style_tone,
            style_format=style_format,
            memory_context=memory_context,
            has_manual="pdf_ref" in st.session_state
        )
        
        model = genai.GenerativeModel("gemini-2.0-flash-exp", system_instruction=sys_prompt, tools=tools)
        
        req = [prompt]
        if "pdf_ref" in st.session_state:
            req.append(st.session_state.pdf_ref)
        if "current_audio_path" in st.session_state:
            audio_path = st.session_state.current_audio_path
            mime = get_mime_type(audio_path)
            audio_data = pathlib.Path(audio_path).read_bytes()
            req.append({"mime_type": mime, "data": audio_data})
            # Ne force PAS l'analyse, laisse Claude décider si c'est pertinent

        with st.chat_message("assistant"):
            try:
                resp = model.generate_content(req)
                text_resp = resp.text
                
                st.markdown(text_resp)
                st.session_state.chat_history.append({"role": "assistant", "content": text_resp})
            except Exception as e:
                st.error(f"Erreur IA : {e}" if lang == "Français 🇫🇷" else f"AI Error: {e}")

else:
    st.sidebar.warning("🔑 Clé API requise / API Key needed")