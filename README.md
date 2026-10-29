# AutoPrésentation

**AutoPrésentation** est un logiciel Windows qui crée une présentation à votre place : vous écrivez un sujet, l'IA **Gemini** (clé gratuite) prépare le plan, puis le logiciel **pilote Microsoft PowerPoint** : les diapositives apparaissent une à une, le fichier `.pptx` est enregistré et, si vous le souhaitez, le **diaporama se lance tout seul**.

> Le sujet que vous écrivez est envoyé à Google (API Gemini). N'y mettez pas d'informations confidentielles (surtout avec la clé gratuite).

## 1. Obtenir le logiciel (sans installer Python)

La compilation se fait dans le cloud, sur les ordinateurs de GitHub.

### Étape A : créer le dépôt
1. Sur <https://github.com>, cliquez sur **New**. Nom : `AutoPresentation`. Ne cochez aucune case (README, .gitignore). **Create repository**.

### Étape B : envoyer les fichiers
Décompressez le zip, ouvrez un terminal **dans le dossier `AutoPresentation`**, puis :

```
git init
git add .
git commit -m "Premier envoi"
git branch -M main
git remote add origin https://github.com/VOTRE_PSEUDO/AutoPresentation.git
git push -u origin main
```

*(Sans Git : « uploading an existing file », puis glissez le **contenu** du dossier. Le dossier caché `.github` doit être envoyé : dans l'Explorateur, Affichage → Éléments masqués.)*

### Étape C : compilation
Elle démarre toute seule après l'envoi. Sinon : onglet **Actions** → **Compiler AutoPresentation (Windows)** → **Run workflow**. Une pastille verte ✔ = succès.

### Étape D : télécharger
Dans **Actions**, ouvrez la compilation verte, section **Artifacts**, téléchargez **AutoPresentation-Windows**, extrayez le zip : vous obtenez `AutoPresentation.exe`.

## 2. Clé Gemini gratuite
1. Allez sur <https://aistudio.google.com/apikey> et créez une clé.
2. Dans le logiciel : **Paramètres (clé Gemini)** → collez la clé → **Enregistrer**.

La clé est enregistrée **uniquement sur votre PC** (`%APPDATA%\AutoPresentation\reglages.json`, en clair) ; elle n'est jamais dans le logiciel ni sur GitHub. Ne la partagez avec personne.

## 3. Utilisation
1. Lancez `AutoPresentation.exe`.
2. Écrivez le **sujet** (vous pouvez ajouter des consignes : public visé, ton, points à couvrir).
3. Réglez le nombre de diapositives, le thème, la pause entre diapositives, le lancement du diaporama et le passage automatique (secondes, 0 = vous passez les diapositives vous-même).
4. Cliquez sur **Créer la présentation**. PowerPoint s'ouvre et se remplit. Ne touchez pas à PowerPoint pendant la création.
5. Le fichier est enregistré dans votre dossier Documents (modifiable dans les Paramètres).

Le bouton **Arrêter** interrompt la création (la présentation partielle reste ouverte, non enregistrée).

## 4. Limites à connaître
- Windows + **PowerPoint de bureau** installé (la version web ne peut pas être pilotée).
- Internet requis. La clé gratuite a des limites (requêtes par minute et par jour) qui peuvent changer ; une seule requête est utilisée par présentation, et le logiciel réessaie automatiquement si la limite est atteinte.
- Le modèle par défaut est `gemini-flash-latest` ; si un modèle est introuvable, le logiciel en choisit automatiquement un autre disponible pour votre clé.
- Le contenu est généré par une IA : **relisez-le**, vérifiez les faits et les chiffres.
- Le `.exe` n'est pas signé : Windows SmartScreen peut afficher un avertissement (**Informations complémentaires** → **Exécuter quand même**). Ne désactivez pas Windows Defender. L'empreinte SHA-256 est fournie (`AutoPresentation.exe.sha256.txt`) ; vérification : `Get-FileHash .\AutoPresentation.exe`.
- **Testé automatiquement** : lecture du plan, appels Gemini simulés, construction PowerPoint simulée, gestion des erreurs. **Non testé automatiquement** : l'interface graphique et le pilotage réel de PowerPoint, qui ne se valident que sur un vrai Windows avec PowerPoint. Faites un premier essai (3 diapositives) et, en cas de problème, copiez le message affiché.

## 5. Problèmes fréquents
| Problème | Solution |
|---|---|
| « Clé Gemini refusée » | Recréez une clé dans Google AI Studio et collez-la dans les Paramètres. |
| « Modèle Gemini introuvable » | Mettez le nom d'un modèle gratuit actuel dans les Paramètres. |
| « Limite de requêtes gratuites atteinte » | Attendez une minute (ou demain si le quota du jour est épuisé). |
| « PowerPoint est introuvable » | Installez PowerPoint de bureau. |
| « PowerPoint a signalé une erreur » | Fermez les boîtes de dialogue ouvertes dans PowerPoint, puis recommencez. |
| Compilation GitHub rouge | Ouvrez l'étape en échec dans Actions et copiez le message d'erreur. |

## 6. Structure
```
app.py                    point d'entrée
autopresentation/         code (interface, gemini, plan, powerpoint, moteur, config, style)
tests/                    tests automatisés
AutoPresentation.spec     configuration PyInstaller
.github/workflows/        compilation automatique GitHub Actions
```
Tests : `python -m unittest discover -s tests -t . -v`
