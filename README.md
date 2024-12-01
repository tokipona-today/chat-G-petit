# chat-G-petit
Une démonstration simple d'un modèle de langage basique, créée à des fins pédagogiques.

## Description

Cette application propose deux démonstrations :
1. Prédiction mot à mot : l'utilisateur et le modèle écrivent une phrase en alternance
2. Génération de phrases : le modèle génère une phrase complète contenant un mot donné

## Installation locale

1. Clonez le repository :
```bash
git clone https://github.com/VOTRE_USERNAME/mini-llm-demo.git
cd mini-llm-demo
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancez l'application :
```bash
streamlit run app.py
```

## Structure du projet

```
mini-llm-demo/
│
├── app.py            # Application principale
├── texte.txt         # Texte d'entraînement par défaut
├── requirements.txt  # Dépendances Python
└── README.md        # Ce fichier
```

## Utilisation

1. L'application démarre avec un texte d'entraînement préchargé
2. Vous pouvez utiliser votre propre fichier texte via l'option dans la barre latérale
3. Choisissez entre les deux modes de démonstration
4. Pour la prédiction mot à mot :
   - Écrivez un mot
   - Le modèle prédit le mot suivant
   - Et ainsi de suite...
5. Pour la génération de phrases :
   - Entrez un mot thème
   - Le modèle génère une phrase contenant ce mot

