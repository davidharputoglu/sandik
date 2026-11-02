# Contribuer à sandik

Merci de votre intérêt ! Les contributions sont bienvenues : corrections, traductions, modules métiers.

1. **Accord de contributeur.** Avant qu'une contribution soit acceptée, vous devez accepter l'[accord de
   contributeur (CLA)](CLA.md), en l'indiquant dans votre demande de fusion (pull request) :
   > J'ai lu et j'accepte l'accord de contributeur de sandik (CLA.md).
2. **Traductions.** Les fichiers sont dans `frontend/src/i18n/<langue>.json`. Le français (`fr.json`) est la
   référence. `npm run i18n:check` liste les clés manquantes.
3. **Modules métiers.** Ils vivent dans le dépôt des modules (`sandik-modules`). Partez du module `modele`.
4. **Tests.** `pytest` doit passer. Ajoutez un test pour toute règle métier (numérotation, TVA, mentions).
5. **Style.** Code et commentaires en français, noms simples, pas de dépendance inutile.

Contact : David HARPUTOGLU — kasparof57@gmail.com
