import streamlit as st
from collections import defaultdict
import random
import pandas as pd
import re


class SimpleLLM:
    def __init__(self):
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.vocabulary = set()
        self.starts = defaultdict(int)

    def clean_word(self, word):
        """Nettoie un mot en gardant intactes les apostrophes"""
        # Enlève uniquement les nombres et la ponctuation (sauf apostrophes)
        # et les tirets qui ne font pas partie d'un mot
        word = re.sub(r'[0-9]', '', word)
        word = re.sub(r'[!?,.:;"]', '', word)
        return word.lower()

    def clean_text(self, text):
        """Nettoie le texte et le découpe en phrases"""
        # Séparer en phrases (uniquement sur les points)
        phrases = re.split(r'\.', text)

        # Nettoyer chaque phrase
        cleaned_phrases = []
        for phrase in phrases:
            # Split en gardant les apostrophes
            words = phrase.strip().split()
            if not words:
                continue

            # Nettoyer chaque mot
            cleaned_words = [self.clean_word(word) for word in words]
            cleaned_words = [w for w in cleaned_words if w]

            if cleaned_words:
                cleaned_phrases.append(cleaned_words)

        return cleaned_phrases

    def train(self, text):
        # Nettoyer et séparer le texte en phrases
        cleaned_phrases = self.clean_text(text)

        # Traitement des phrases
        for words in cleaned_phrases:
            if not words:
                continue

            # Stocker le premier mot comme début de phrase
            self.starts[words[0]] += 1

            # Ajouter les mots au vocabulaire
            self.vocabulary.update(words)

            # Construire les transitions
            for i in range(len(words) - 1):
                current_word = words[i]
                next_word = words[i + 1]
                self.transitions[current_word][next_word] += 1

        # Afficher les statistiques
        st.sidebar.write(f"Nombre de phrases apprises : {len(cleaned_phrases)}")

    def select_weighted(self, frequency_dict):
        """Sélectionne un mot en fonction de ses fréquences"""
        words = list(frequency_dict.keys())
        weights = list(frequency_dict.values())
        total = sum(weights)
        probabilities = [w/total for w in weights]
        return random.choices(words, probabilities)[0]

    def predict_next(self, word):
        word = self.clean_word(word)
        if word in self.transitions:
            prediction = self.select_weighted(self.transitions[word])
            suivants = [(w, f) for w, f in self.transitions[word].items()]
            suivants = sorted(suivants, key=lambda x: x[1], reverse=True)
            return prediction, suivants
        return "Je ne connais pas ce mot...", []

    def generate_sentence(self, theme_word):
        theme_word = self.clean_word(theme_word)
        if theme_word not in self.vocabulary:
            return "Je ne connais pas ce mot..."

        sentence = [self.select_weighted(self.starts)]
        max_length = 15
        theme_used = False

        while len(sentence) < max_length:
            current_word = sentence[-1]

            if not theme_used and len(sentence) > 2:
                sentence.append(theme_word)
                theme_used = True
                continue

            if current_word not in self.transitions:
                break

            next_word = self.select_weighted(self.transitions[current_word])
            sentence.append(next_word)

            if not self.transitions[next_word]:
                break

        if not theme_used:
            sentence.insert(random.randint(1, len(sentence)), theme_word)

        return ' '.join(sentence).capitalize() + '.'


def load_text_from_file(uploaded_file):
    try:
        return uploaded_file.getvalue().decode('utf-8')
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {str(e)}")
        return None


def chat_demo():
    MAX_EXCHANGES = 4  # Nombre d'échanges à garder

    if not st.session_state.trained:
        st.info("👈 Commencez par charger un fichier d'entraînement dans la barre latérale")
    else:
        container = st.container()
        col1, col2 = container.columns([3, 1])

        with col1:
            chat_container = st.container()
            input_container = st.container()

            with chat_container:
                # Ne garder que les derniers messages
                start_idx = max(0, len(st.session_state.messages) - (MAX_EXCHANGES * 2))
                recent_messages = st.session_state.messages[start_idx:]

                for message in recent_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"]["text"])

            with input_container:
                if prompt := st.chat_input("Entrez un mot...", key="chat_input"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": {"text": prompt}
                    })

                    prediction, suivants = st.session_state.llm.predict_next(prompt)
                    st.session_state.current_possibilities = suivants
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": {"text": prediction}
                    })
                    st.rerun()

        with col2:
            if st.session_state.current_possibilities:
                st.markdown("### Mots possibles")
                df = pd.DataFrame(st.session_state.current_possibilities,
                                  columns=['Mot suivant', 'Fréquence'])
                st.dataframe(df, hide_index=True)


def sentence_demo():
    if not st.session_state.trained:
        st.info("👈 Commencez par charger un fichier d'entraînement dans la barre latérale")
    else:
        theme = st.text_input("Entrez un thème (un mot) :")
        if theme:
            sentence = st.session_state.llm.generate_sentence(theme)
            st.write(sentence)


def main():
    st.title("Mini-LLM : Démonstration")

    # Initialisation de la session state
    if 'llm' not in st.session_state:
        st.session_state.llm = SimpleLLM()
    if 'trained' not in st.session_state:
        st.session_state.trained = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_possibilities' not in st.session_state:
        st.session_state.current_possibilities = []
    if 'using_default_text' not in st.session_state:
        st.session_state.using_default_text = True

    # Sidebar pour l'entraînement
    with st.sidebar:
        st.header("Configuration du modèle")

        # Option pour utiliser son propre fichier
        use_custom_file = st.checkbox("Utiliser mon propre fichier texte", value=False)

        if use_custom_file:
            uploaded_file = st.file_uploader("Charger votre fichier texte", type=['txt'])
            if uploaded_file and st.session_state.using_default_text:
                text = load_text_from_file(uploaded_file)
                if text:
                    st.session_state.llm = SimpleLLM()  # Réinitialiser le modèle
                    st.session_state.llm.train(text)
                    st.session_state.trained = True
                    st.session_state.using_default_text = False
                    st.session_state.messages = []  # Réinitialiser la conversation
                    st.success(
                        f"✅ Modèle entraîné avec votre fichier! ({len(st.session_state.llm.vocabulary)} mots connus)")
                    with st.expander("Voir le texte d'entraînement"):
                        st.text(text)
        elif not st.session_state.trained or not st.session_state.using_default_text:
            # Charger le texte par défaut
            try:
                with open('texte.txt', 'r', encoding='utf-8') as file:
                    default_text = file.read()
                st.session_state.llm = SimpleLLM()  # Réinitialiser le modèle
                st.session_state.llm.train(default_text)
                st.session_state.trained = True
                st.session_state.using_default_text = True
                st.session_state.messages = []  # Réinitialiser la conversation
                st.success("✅ Modèle entraîné avec le texte par défaut")
                with st.expander("Voir le texte d'entraînement"):
                    st.text(default_text)
            except FileNotFoundError:
                st.error("Erreur: Le fichier texte.txt n'a pas été trouvé")

        if st.session_state.trained:
            st.metric("Taille du vocabulaire", f"{len(st.session_state.llm.vocabulary)} mots")

        st.markdown("---")

        if st.session_state.messages:
            if st.button("🗑️ Réinitialiser la conversation"):
                st.session_state.messages = []
                st.session_state.current_possibilities = []
                st.rerun()

    # Sélection de la démo
    demo = st.radio("Choisir la démonstration :",
                    ["Prédiction mot à mot", "Génération de phrases"],
                    horizontal=True)

    # Afficher la démo sélectionnée
    if demo == "Prédiction mot à mot":
        st.markdown("""
        ### Mode d'emploi
        1. Chargez un fichier texte d'entraînement
        2. Écrivez un mot dans le chat
        3. Le modèle prédit le mot suivant
        4. Écrivez un autre mot
        5. Et ainsi de suite...
        """)
        chat_demo()
    else:
        st.markdown("""
        ### Mode d'emploi
        1. Chargez un fichier texte d'entraînement
        2. Entrez un mot thème
        3. Le modèle génère une phrase contenant ce mot
        """)
        sentence_demo()


if __name__ == "__main__":
    main()
