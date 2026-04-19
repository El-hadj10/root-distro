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

1. Le script affichera les informations système collectées via adb.
2. Un rapport JSON sera aussi genere dans `reports/latest_audit.json`.

## Options utiles

Auditer un appareil precis :

```bash
python3 scripts/audit_android.py --serial NUMERO_DE_SERIE
```

Choisir un chemin de sortie different pour le rapport JSON :

```bash
python3 scripts/audit_android.py --output reports/mon_rapport.json
```

## Résultat attendu

- Liste des appareils connectés
- Version Android
- Version SDK
- Modele et marque
- Version du bootloader
- Version du kernel
- Etat SELinux
- Présence ou non d’un binaire su (root)

## Depannage

- Si l'appareil apparait comme `unauthorized`, validez l'empreinte adb sur le telephone.
- Si aucun appareil n'apparait, verifiez le cable USB et le mode de connexion.
- Si `adb` n'est pas trouve, assurez-vous qu'il est bien installe et disponible dans le PATH.

---

Pour toute contribution, voir le README principal.
