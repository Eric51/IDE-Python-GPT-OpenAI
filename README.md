# IDE-Python-GPT-OpenAI
Ce programme est un IDE simplifié pour le langage de programmation Python. Il vous permet de créer, éditer, exécuter et enregistrer des fichiers Python. Il utilise la bibliothèque PyQt5 pour l'interface utilisateur et différentes bibliothèques pour des fonctionnalités spécifiques telles que la coloration syntaxique, la numérotation des lignes et la recherche/remplacement de texte dans l'éditeur. 

Il inclut également une fonction d'interaction avec l'API OpenAI pour générer des réponses à partir d'une entrée en utilisant les modèles GPT-4 et GPT-3.5. L'interface utilisateur comprend un champ de texte pour l'entrée du prompt, un bouton pour envoyer le prompt au modèle GPT, un champ pour afficher les réponses générées et un bouton pour copier le code généré dans le presse-papiers.

Le programme offre également des options de configuration pour personnaliser l'apparence et le comportement de l'IDE, notamment la police, la taille de police, le modèle GPT et l'API Key OpenAI utilisés par le programme.


Voici les bibliothèques que vous devez installer pour utiliser ce programme :

- json : Bibliothèque standard de Python, pas besoin de l'installer.
- os : Bibliothèque standard de Python, pas besoin de l'installer.
- re : Bibliothèque standard de Python pour les expressions régulières, pas besoin de l'installer.
- numpy : Une bibliothèque pour le calcul scientifique. Vous pouvez l'installer avec la commande `pip install numpy`
- openai : La bibliothèque de l'API d'OpenAI, vous pouvez l'installer avec `pip install openai`
- pygments : Une bibliothèque de coloration syntaxique. Vous pouvez l'installer avec `pip install pygments`
- PyQt5 : Une bibliothèque pour la création d'interfaces utilisateur. Vous pouvez l'installer avec `pip install pyqt5`
- sys : Bibliothèque standard de Python, pas besoin de l'installer.
- subprocess : Bibliothèque standard de Python, pas besoin de l'installer.
- tempfile : Bibliothèque standard de Python, pas besoin de l'installer.
- pickle : Bibliothèque standard pour la sérialisation d'objets en Python, pas besoin de l'installer.
- collections : Bibliothèque standard pour les structures de données, pas besoin de l'installer.

Voici une commande qui installera toutes les bibliothèques nécessaires qui ne sont pas déjà incluses dans la bibliothèque standard de Python :
```
pip install numpy openai pygments pyqt5
```
