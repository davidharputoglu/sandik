# Sécurité / Security

Pour signaler une faille de sécurité, **n'ouvrez pas de ticket public** : écrivez à
**kasparof57@gmail.com** avec une description du problème et, si possible, les étapes pour le reproduire.
Vous recevrez une réponse dès que possible.

Bonnes pratiques d'installation :
- en Docker / serveur, laissez la connexion activée (`SANDIK_AUTH=1`, par défaut) ;
- placez sandik derrière un proxy HTTPS (Traefik, Caddy, Nginx Proxy Manager…) et activez `SANDIK_COOKIE_SECURE=1` ;
- sauvegardez régulièrement le volume `/data` et la base de données ;
- n'importez que des modules de confiance.

*To report a vulnerability, email kasparof57@gmail.com instead of opening a public issue.*
