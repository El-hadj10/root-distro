# Guide de flash securise

Ce guide ajoute un flux de flash fastboot avec garde-fous. Il est destine au reflash d'un appareil compatible avec un firmware officiel ou explicitement prevu pour ce modele exact.

## Limites de securite

- Le script refuse le cross-flash si le produit fastboot detecte ne correspond pas au manifeste.
- Le script reste en simulation par defaut.
- Les partitions critiques exigent une confirmation supplementaire.
- Un bootloader verrouille bloque l'execution reelle.

## Prerequis

- fastboot installe et accessible dans le PATH
- Appareil demarre en mode bootloader ou fastboot
- Firmware officiel extrait localement
- Manifeste JSON conforme a l'exemple dans firmware/manifest.example.json

## Simulation d'un flash

Depuis la racine du projet :

```bash
python3 scripts/flash_android.py firmware/manifest.example.json
```

Le script affiche alors :

- l'appareil fastboot detecte
- le produit detecte
- les images a flasher
- les erreurs de compatibilite si presentes

Pour valider uniquement le manifeste et la presence attendue des fichiers, sans appareil fastboot :

```bash
python3 scripts/flash_android.py firmware/manifest.example.json --manifest-only
```

## Execution reelle

Le flash reel demande une confirmation explicite :

```bash
python3 scripts/flash_android.py firmware/manifest.example.json --execute --allow-critical --i-understand-risks
```

## Recommandations

- Utiliser uniquement un bundle correspondant exactement au modele cible.
- Ne jamais flasher vers un autre appareil ou un produit different.
- Verifier au moins une fois le plan en mode simulation avant toute execution reelle.
- Conserver une copie des images d'origine et de la documentation constructeur.
