# Guide d’utilisation – Audit Android

Ce guide explique comment utiliser le script d’audit fourni dans ce projet.

## Prérequis
- Python 3 installé
- adb installé et accessible dans le PATH
- Un appareil Android connecté avec le débogage USB activé

## Utilisation du script

1. Connectez votre appareil Android au PC via USB.
2. Activez le débogage USB sur l’appareil (Paramètres > À propos du téléphone > Appuyez 7 fois sur Numéro de build, puis retournez dans Paramètres > Options pour les développeurs > Activez Débogage USB).
3. Exécutez le script :

```bash
python3 scripts/audit_android.py
```

4. Le script affichera les informations système collectées via adb.

## Résultat attendu
- Liste des appareils connectés
- Version Android
- Version du bootloader
- Présence ou non d’un binaire su (root)

---

Pour toute contribution, voir le README principal.