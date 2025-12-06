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

# --- 3. DICTIONNAIRE RICHE  ---
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
        "memory_title": "💾 Session & Mémoire",
        "memory_load": "📂 Reprendre une session précédente",
        "memory_help": "💡 Comment ça marche ?",
        "memory_desc": "1. En fin de session, cliquez sur **Télécharger Session** en bas\n2. La prochaine fois, glissez ce fichier .txt ici pour continuer",
        "memory_save": "💾 Télécharger Session",
        "reset": "Nouvelle Session",
        "about": "Philosophie du projet",
        "about_text": "**Groovebox Tutor** est un projet libre, né du désir de reconnecter les musiciens avec leurs machines.\n\nNotre but n'est pas de copier, mais de **comprendre**. L'IA agit comme un binôme technique : elle écoute, lit la doc, et vous explique *comment* sculpter votre propre son.\n\nL'outil est gratuit. Si vous apprenez des choses grâce à lui, vous pouvez me soutenir.",
        "support": "Soutenir (Don)",
        "title": "Groovebox Tutor",
        "subtitle": "Votre binôme technique. Décryptez le son. Maîtrisez votre machine.",
        "placeholder": "Posez une question technique sur ce son...",
        "onboarding": "👋 **Objectif : Autonomie**\n1. Importez le **Manuel** de votre instrument (à gauche).\n2. Proposez un **Son** qui vous inspire (ci-dessous).\n3. Votre binôme analyse la texture et vous enseigne **les étapes techniques** pour recréer ce grain vous-même.",
        "legal": "⚠️ Outil d'analyse à but éducatif. L'inspiration est légale, le plagiat ne l'est pas.",
        "sugg_1": "Analyse ce son",
        "sugg_2": "Structure rythmique",
        "sugg_3": "Fonction cachée",
        "style_label": "Approche Pédagogique",
        "tones": ["🤙 Mentor Cool", "👔 Expert Technique", "⚡ Synthétique"],
        "formats": ["📝 Cours Complet", "✅ Checklist", "💬 Interactif"],
        "manual_loaded": "✅ Manuel assimilé",
        "active_track": "Piste active :"
    },
    # (Je garde l'Anglais pour la structure, les autres langues suivront ce modèle riche si tu les déploies)
    "English 🇬🇧": {"settings": "1. Setup", "api_label": "Google API Key", "api_help": "Why a personal key?", "api_desc": "Open-source project. Using your own free key ensures your independence.", "doc_section": "2. Your Gear", "doc_help": "Find official manual", "manual_upload": "Drop PDF Manual here", "audio_title": "🎧 The Sound", "audio_subtitle": "Magic happens here. Drop your audio file.", "audio_label": "Audio File", "memory_title": "Advanced (Memory)", "memory_load": "Load Session", "memory_save": "Save Session", "reset": "New Session", "about": "Project Philosophy", "about_text": "**Groovebox Tutor** is a free project.\nOur goal isn't to copy, but to **understand**. The AI acts like a technical partner.", "support": "Donate", "title": "Groovebox Tutor", "subtitle": "Your technical partner. Decode sound. Master your gear.", "placeholder": "Ask a question...", "onboarding": "👋 **Goal: Autonomy**\n1. Upload your instrument's **Manual**.\n2. Provide a **Sound** that inspires you.\n3. Your partner analyzes the texture and teaches you **the technical steps**.", "legal": "Educational tool. Inspiration is legal, plagiarism is not.", "sugg_1": "Analyze sound", "sugg_2": "Rhythm", "sugg_3": "Feature", "style_label": "Tutor Style", "tones": ["🤙 Cool Mentor", "👔 Technical Expert", "⚡ Direct"], "formats": ["📝 Full Lesson", "✅ Checklist", "💬 Interactive"], "manual_loaded": "✅ Manual loaded", "active_track": "Track:"}
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
        "🤙 Cool Mentor": {
            "voice": "Ton décontracté, tutoiement, encourage l'expérimentation sans jugement",
            "examples": "Utilise des analogies fun (ex: 'ce filtre agit comme un robinet qui laisse passer seulement les aigus')",
            "energy": "Enthousiaste, ponctue avec des emojis musicaux 🎛️🔊"
        },
        "👔 Technical Expert": {
            "voice": "Ton professionnel mais accessible, vouvoiement possible, précis dans les termes",
            "examples": "Cite des références techniques précises, utilise le vocabulaire exact du fabricant",
            "energy": "Rigoureux mais pédagogue, structure claire"
        },
        "⚡ Direct": {
            "voice": "Ton synthétique, va droit au but, pas de blabla",
            "examples": "Donne les infos essentielles, bullet points si nécessaire",
            "energy": "Efficace, minimaliste"
        },
        "🤙 Cool Mentor": {  # English
            "voice": "Casual tone, first names, encourage experimentation without judgment",
            "examples": "Use fun analogies (e.g., 'this filter acts like a tap letting only highs through')",
            "energy": "Enthusiastic, use music emojis 🎛️🔊"
        },
        "👔 Technical Expert": {  # English
            "voice": "Professional yet accessible, precise terminology",
            "examples": "Cite precise technical references, use manufacturer's exact vocabulary",
            "energy": "Rigorous but pedagogical, clear structure"
        },
        "⚡ Direct": {  # English
            "voice": "Synthetic, straight to the point, no fluff",
            "examples": "Give essential info, bullet points if needed",
            "energy": "Efficient, minimalist"
        }
    }
    
    # Mapping des formats
    FORMAT_PROFILES = {
        "📝 Full Lesson": "Explications détaillées en prose, structure pédagogique avec intro/concept/pratique/conclusion",
        "✅ Checklist": "Listes numérotées et bullet points, étapes concrètes à suivre, format actionnable",
        "💬 Interactive": "Questions ouvertes fréquentes, dialogue socratique, invite l'utilisateur à réfléchir avant de donner la réponse",
        "📝 Full Lesson": "Detailed prose explanations, pedagogical structure with intro/concept/practice/conclusion",  # English
        "✅ Checklist": "Numbered lists and bullets, concrete steps, actionable format",  # English
        "💬 Interactive": "Frequent open questions, Socratic dialogue, invite reflection before answers"  # English
    }
    
    tone_profile = TONE_PROFILES.get(style_tone, TONE_PROFILES["🤙 Cool Mentor"])
    format_profile = FORMAT_PROFILES.get(style_format, FORMAT_PROFILES["📝 Full Lesson"])
    
    sys_prompt = f"""
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
{"""
- Citer les sections/pages précises pour chaque concept
- Adapter ton vocabulaire aux termes exacts du fabricant
- Identifier les features spécifiques de cette machine
- Montrer OÙ trouver chaque paramètre dans l'interface
- Utiliser les noms de modes/algorithmes propres à cette machine

**Exemple :**
"Pour ce filtre, consulte page 42 section FILTER TYPE — le Digitakt utilise un filtre 2-pôles avec résonance variable. Tu le trouveras en appuyant sur [FUNC] + [TRIG]."
""" if has_manual else """
- Expliquer les concepts universels de synthèse
- Donner des exemples applicables à la plupart des machines
- Rester sur les principes théoriques sans citer de pages
- Encourager l'utilisateur à chercher dans SON manuel si disponible

**Exemple :**
"Ce type de filtre passe-bas avec résonance est standard sur la plupart des grooveboxes. Cherche dans ton manuel les sections 'FILTER' ou 'SYNTH ENGINE'."
"""}

---

# 🎓 MÉTHODOLOGIE PÉDAGOGIQUE

## ❌ CE QUE TU NE FAIS JAMAIS
- Donner les valeurs exactes des paramètres (ex: "Cutoff = 63")
- Fournir un preset clé-en-main
- Juste décrire sans expliquer le "pourquoi"
- Copier-coller des passages du manuel (reformule toujours)

## ✅ CE QUE TU FAIS TOUJOURS
- Expliquer la LOGIQUE du son (relation cause-effet)
- Guider par des questions ouvertes {" surtout en mode 💬 Interactive" if style_format == "💬 Interactive" else ""}
- Proposer des expérimentations à faire
- Donner des fourchettes de valeurs ("entre 40% et 70%")
- Utiliser des analogies concrètes adaptées à la culture {lang.split()[0]}

---

# 📐 STRUCTURE DE RÉPONSE

{"### Format PROSE (Full Lesson)" if style_format == "📝 Full Lesson" else ""}
{"### Format CHECKLIST (actionnable)" if style_format == "✅ Checklist" else ""}
{"### Format INTERACTIF (Socratique)" if style_format == "💬 Interactive" else ""}

{"""
**Étape 1 : Observation initiale**
Décris ce que tu entends (vocabulaire technique accessible).
Ex: "J'entends un son percussif avec une fondamentale autour de 60Hz, une attack très rapide, et une texture granuleuse suggérant du bit crushing."

**Étape 2 : Question ouverte**
Engage la réflexion de l'utilisateur.
Ex: "Toi, qu'est-ce qui fait l'identité de ce son selon toi ?"

**Étape 3 : Explication conceptuelle**
Explique les mécanismes en jeu avec références au manuel.
Ex: "Cette texture métallique vient d'un filtre HP avec forte résonance. [Si manuel : Page 38, section FILTER TYPES]."

**Étape 4 : Guide d'expérimentation**
Donne des pistes sans donner la solution.
Ex: "Pour recréer ça :
- Commence avec une onde triangle
- Applique un filtre HP et monte la résonance progressivement
- Façonne l'envelope pour une attack instantanée
→ Teste et dis-moi ce qu'il manque encore."

**Étape 5 : Check-in**
Invite au retour d'expérience.
Ex: "Fais ces ajustements et reviens vers moi avec tes résultats !"
""" if style_format == "📝 Full Lesson" else ""}

{"""
**Format : Liste d'actions concrètes**

✅ **ANALYSE** (ce que tu détectes)
- Point clé 1
- Point clé 2

✅ **CONCEPTS** (théorie express)
- Principe 1 → référence manuel si dispo
- Principe 2

✅ **ACTIONS** (étapes à suivre)
1. Première manip
2. Deuxième manip
3. Affinage

✅ **CHECK** (validation)
→ "Teste et vérifie si tu obtiens [résultat attendu]"
""" if style_format == "✅ Checklist" else ""}

{"""
**Format : Dialogue + Questions**

🔊 **Observation** : "Voici ce que j'entends..."

❓ **Question 1** : "Qu'est-ce qui te saute aux oreilles ?"
[Attends la réponse implicitement]

💡 **Explication** (après réflexion de l'user)
"Exactement ! Ce que tu identifies là, c'est..."

🧪 **Expérimentation guidée**
"Maintenant essaie ceci... Qu'est-ce que ça change ?"

🔄 **Itération**
"Parfait ! Et si tu modifiais [paramètre], que se passerait-il selon toi ?"
""" if style_format == "💬 Interactive" else ""}

---

# 🧠 PRINCIPES PÉDAGOGIQUES

1. **Autonomie > Solution rapide**
   Goal = COMPRENDRE la synthèse, pas copier un preset.

2. **Apprentissage par l'erreur**
   Encourage les tests ratés : "Qu'as-tu appris ?"

3. **Analogies culturelles**
   Adapte tes métaphores à {lang} :
   - Filtre = robinet, tamis, filtre à café
   - Envelope = courbe de rebond de balle
   - Résonance = corde de guitare qui vibre

4. **Progressivité**
   Layer 1 : Son de base (oscillateur + filtre)
   Layer 2 : Envelope pour le timbre
   Layer 3 : Modulations (LFO, vélocité)
   Layer 4 : Effets et spatialisation

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

# 💡 EXEMPLES CONCRETS (adapte au style choisi)

{"## Exemple 1 : Bass Synthétique (Cool Mentor + Full Lesson)" if style_tone == "🤙 Cool Mentor" and style_format == "📝 Full Lesson" else ""}
{"## Exemple 1 : Bass Synthétique (Technical Expert + Checklist)" if style_tone == "👔 Technical Expert" and style_format == "✅ Checklist" else ""}
{"## Exemple 1 : Bass Synthétique (Direct + Interactive)" if style_tone == "⚡ Direct" and style_format == "💬 Interactive" else ""}

{"""
🔊 Yo ! J'écoute ta bass et franchement, c'est costaud ! 🎛️

Ce qui me saute aux oreilles :
- Une **subbass bien grasse** qui tient le grave
- Un **mouvement dans les médiums** qui fait ce fameux "wob wob"
- Une **attack assez lente**, ça donne ce côté hypnotique

Toi, qu'est-ce qui te frappe le plus dans ce son ?

---

**Le truc technique :**
Ce mouvement, c'est un **LFO qui module le filtre**. Imagine un robinet qui s'ouvre/ferme en rythme — c'est exactement ça ! Le filtre laisse passer plus ou moins d'aigus selon la position du LFO.

[Manuel page 56, section LFO DESTINATIONS]

---

**Allez, on expérimente !**
1. Pars d'une **onde carrée ou saw** bien grave (sub)
2. Claque un **filtre passe-bas**, cutoff vers 30-40%
3. Assigne un **LFO triangle** au cutoff, vitesse 1/8 ou 1/16
4. Monte la **profondeur du LFO** jusqu'à sentir le balayage

Lance ça et dis-moi ce qu'il manque encore ! 🚀
""" if style_tone == "🤙 Cool Mentor" and style_format == "📝 Full Lesson" else ""}

{"""
✅ **ANALYSE AUDIO**
- Subbass : fondamentale ~50Hz
- Modulation : filter sweep rythmique
- Attack : lente (~50ms)

✅ **CONCEPT CLÉ**
- LFO → Filter Cutoff (mouvement wob-wob)
- Référence : Manuel page 56, LFO DESTINATIONS

✅ **ACTIONS**
1. Oscillateur : onde carrée/saw, tune -2 octaves
2. Filtre LP : cutoff 30-40%, résonance 20-30%
3. LFO : forme triangle, destination = cutoff, rate = 1/8
4. Profondeur LFO : augmenter jusqu'à obtenir le balayage

✅ **VALIDATION**
→ Le mouvement doit être audible. Si trop subtil, augmente la profondeur LFO ou la résonance du filtre.
""" if style_tone == "👔 Technical Expert" and style_format == "✅ Checklist" else ""}

{"""
🔊 Bass avec mouvement médium-aigu. Attack lente.

❓ **Qu'est-ce qui crée ce mouvement selon toi ?**

💡 C'est un LFO sur le filtre cutoff.

🧪 **Test :**
1. Onde saw, filtre LP cutoff 40%
2. LFO triangle → cutoff, rate 1/8

❓ **Ça bouge assez ?**
→ Sinon : monte profondeur LFO ou résonance.
""" if style_tone == "⚡ Direct" and style_format == "💬 Interactive" else ""}

---

Prêt à analyser ton premier son ! 🎧
"""
    
    return sys_prompt

# --- 5. INTERFACE ---

# --- SIDEBAR ---
with st.sidebar:
    lang = st.selectbox("Langue / Language", list(TR.keys()), label_visibility="collapsed")
    T = TR.get(lang, TR["Français 🇫🇷"])
    
    # 1. SETUP
    st.markdown(f"### {T['settings']}")
    api_key = st.text_input(T["api_label"], type="password", placeholder="AIzaSy...")
    with st.expander(T["api_help"]):
        st.caption(T["api_desc"])
        st.markdown("[Google AI Studio](https://aistudio.google.com/) (Free)")

    st.markdown("---")
    
    # 2. MACHINE (MANUEL)
    st.markdown(f"### {T['doc_section']}")
    
    # HELPER COMPLET (Tes 7 liens sont là)
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
    
    uploaded_pdf = st.file_uploader(T["manual_upload"], type=["pdf"], label_visibility="collapsed")
    if uploaded_pdf:
        st.success(T["manual_loaded"])

    st.markdown("---")
    
    # 3. STYLE PÉDAGOGIQUE
st.markdown("### 3. Style Pédagogique" if lang == "Français 🇫🇷" else "### 3. Teaching Style")
style_tone = st.selectbox("Ton", T["tones"], index=0, label_visibility="collapsed")
style_format = st.radio("Format", T["formats"], index=0, label_visibility="collapsed")

st.markdown("---")

# 4. SESSION & MÉMOIRE
st.markdown(f"### {T['memory_title']}")

with st.expander(T["memory_help"]):
    st.info(T["memory_desc"])

uploaded_memory = st.file_uploader(
    T["memory_load"], 
    type=["txt"], 
    key="mem_up",
    help="Glissez le fichier .txt téléchargé lors d'une session précédente"
)

if uploaded_memory:
    st.session_state.memory_content = uploaded_memory.getvalue().decode("utf-8")
    st.success("✅ Session rechargée ! L'IA se souvient du contexte.")
    
    st.markdown("---")
    
   st.markdown("---")

# FOOTER : ACTIONS
if "chat_history" in st.session_state and st.session_state.chat_history:
    history_txt = format_history(st.session_state.chat_history)
    st.download_button(
        T["memory_save"], 
        history_txt, 
        f"groovebox_session_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", 
        "text/plain", 
        use_container_width=True,
        type="primary"
    )

if st.button(T["reset"], use_container_width=True):
    st.session_state.clear()
    st.rerun()
```

---

## 🎯 Résumé des améliorations

### **Avant** ❌
- Icône `💾` pas claire
- "Reprendre une session" → on comprend pas comment
- Le lien entre télécharger/uploader pas évident

### **Après** ✅
- Section dédiée **"💾 Session & Mémoire"**
- Explications claires dans un expander `💡 Comment ça marche ?`
- Bouton **"💾 Télécharger Session"** visible avec nom de fichier daté
- Message de confirmation quand on upload : **"✅ Session rechargée !"**

---

## 📸 Voilà comment ça va apparaître

**Sidebar :**
```
### 💾 Session & Mémoire

[Expander: 💡 Comment ça marche ?]
  ℹ️ 1. En fin de session, cliquez sur Télécharger Session
     2. La prochaine fois, glissez ce fichier .txt ici

[📂 Reprendre une session précédente]
  Drag & drop zone

---

[💾 Télécharger Session] (bouton bleu/primary)
[Nouvelle Session] (bouton normal)

    with st.expander(T["about"]):
        st.markdown(T["about_text"])
        st.markdown(f"[{T['support']}](https://www.buymeacoffee.com/)")

# --- MAIN AREA ---
st.title(T["title"])
st.markdown(f"<h3 style='margin-top: -20px; margin-bottom: 40px; color: #808080;'>{T['subtitle']}</h3>", unsafe_allow_html=True)

# Onboarding Pédagogique
if not api_key:
    st.info(T["onboarding"])

# ZONE AUDIO
with st.container(border=True):
    st.subheader(T["audio_title"])
    st.caption(T["audio_subtitle"])
    
    uploaded_audio = st.file_uploader(T["audio_label"], type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    
    if not uploaded_audio:
        st.caption(T["legal"])
    
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
        with st.status("Lecture du manuel...", expanded=False) as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t: t.write(uploaded_pdf.getvalue()); p=t.name
            r = upload_pdf_to_gemini(p)
            if r: 
                st.session_state.pdf_ref = r
                status.update(label=T["manual_loaded"], state="complete")

    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    prompt = None
    if not st.session_state.chat_history:
        col1, col2, col3 = st.columns(3)
        if col1.button(T["sugg_1"], type="secondary", use_container_width=True): prompt = T["sugg_1"]
        elif col2.button(T["sugg_2"], type="secondary", use_container_width=True): prompt = T["sugg_2"]
        elif col3.button(T["sugg_3"], type="secondary", use_container_width=True): prompt = T["sugg_3"]

    user_input = st.chat_input(T["placeholder"])
    if user_input: prompt = user_input

    if prompt:
        with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        try: tools = [genai.protos.Tool(google_search=genai.protos.GoogleSearch())]
        except: tools = None
        
        memory_context = ""
        if "memory_content" in st.session_state:
            memory_context = f"## 🧠 CONTEXTE MÉMOIRE\n{st.session_state.memory_content}\n"

        # ✅ UTILISE LA NOUVELLE FONCTION
        sys_prompt = build_system_prompt(
            lang=lang,
            style_tone=style_tone,
            style_format=style_format,
            memory_context=memory_context,
            has_manual="pdf_ref" in st.session_state
        )
        
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
            try:
                resp = model.generate_content(req)
                text_resp = resp.text
                
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
                st.error(f"Erreur IA : {e}")

    if "suggested_theme" in st.session_state and st.session_state.suggested_theme != st.session_state.current_theme:
        with st.container():
            col_msg, col_btn = st.columns([3, 1])
            col_msg.info(f"{T['theme_detected']} **{st.session_state.suggested_theme}**")
            if col_btn.button(T['apply_theme'], use_container_width=True):
                st.session_state.current_theme = st.session_state.suggested_theme
                del st.session_state.suggested_theme
                st.rerun()

else:
    # Warning sidebar si pas de clé
    st.sidebar.warning("🔑 Clé API requise / API Key needed")