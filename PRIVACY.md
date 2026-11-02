# Confidentialité / Privacy

- sandik **ne collecte aucune donnée** : pas de télémétrie, pas de statistiques d'usage, pas de publicité.
- Vos données (clients, devis, factures) restent **sur votre ordinateur ou votre serveur** :
  - bureau : dossier de données de l'utilisateur (`%LOCALAPPDATA%\sandik` sous Windows, `~/.local/share/sandik` sous Linux) ;
  - Docker : le volume `/data` et la base PostgreSQL que vous configurez.
- sandik ne se connecte à aucun service extérieur. Un module importé peut le faire : lisez sa documentation.
- Les mots de passe sont stockés sous forme d'empreinte (scrypt), jamais en clair.
- Vous êtes responsable de traitement pour les données de vos propres clients (RGPD) : sauvegardes,
  durée de conservation, droit d'accès et de rectification.

*sandik collects no data. Everything stays on your computer or server. You are the data controller for
your own customers' data.*
