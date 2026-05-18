import os
import shutil

def run_setup():
    print("=" * 50)
    print("   AUTOMATION DES ÉTAPES GITHUB ACTIONS - LUMIÈRES DE L'AUBE")
    print("=" * 50)
    
    # ÉTAPE 1 : Nettoyage du dossier build de 1.21 Go
    if os.path.exists("build"):
        print("[⏳] Dossier 'build' détecté. Suppression en cours pour alléger le projet...")
        try:
            shutil.rmtree("build")
            print("[✅] ÉTAPE 1 RÉUSSIE : Le dossier 'build' a été entièrement supprimé.")
        except Exception as e:
            print(f"[❌] Erreur lors de la suppression du dossier 'build' : {e}")
            print("    Essayez de fermer VS Code ou tout terminal qui utiliserait ce dossier.")
    else:
        print("[✅] ÉTAPE 1 : Aucun dossier 'build' lourd détecté. Le répertoire est propre.")

    print("-" * 50)

    # ÉTAPE 2 : Création de l'arborescence GitHub et du script Workflow
    workflow_dir = os.path.join(".github", "workflows")
    try:
        os.makedirs(workflow_dir, exist_ok=True)
        print("[✅] Dossier structurel '.github/workflows/' créé.")
    except Exception as e:
        print(f"[❌] Impossible de créer les dossiers : {e}")
        return

    yaml_content = """name: Build Android APK

on:
  push:
    branches:
      - main
      - master
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Set up Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: 'stable'

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flet requests

      - name: Build APK with Flet
        run: |
          flet build apk --permissions location

      - name: Upload APK Artifact
        uses: actions/upload-artifact@v4
        with:
          name: app-release-apk
          path: build/apk/*.apk
"""
    
    workflow_file = os.path.join(workflow_dir, "build-apk.yml")
    try:
        with open(workflow_file, "w", encoding="utf-8") as f:
            f.write(yaml_content)
        print("[✅] Fichier de configuration cloud 'build-apk.yml' écrit.")
    except Exception as e:
        print(f"[❌] Erreur lors de l'écriture du fichier YAML : {e}")
        return

    # Configuration du fichier requirements.txt
    requirements_content = "flet\nrequests\n"
    try:
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)
        print("[✅] ÉTAPE 2 RÉUSSIE : Fichier 'requirements.txt' initialisé à la racine.")
    except Exception as e:
        print(f"[❌] Erreur lors de l'écriture de requirements.txt : {e}")
        return

    print("=" * 50)
    print("🎉 TOUT EST PRÊT ! Les serveurs de GitHub s'occuperont du reste.")
    print("=" * 50)

if __name__ == "__main__":
    run_setup()
