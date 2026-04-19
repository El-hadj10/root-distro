# root-distro

Outil d’audit et de diagnostic Android via adb/fastboot.

## Objectif

Ce projet permet de collecter des informations système sur un appareil Android connecté, de vérifier l’état du bootloader, la présence du root, les partitions, etc. **Aucune opération de contournement ou d’élévation de privilèges n’est réalisée.**

## Structure

- `scripts/` : scripts d’audit (Python, bash)
- `docs/` : documentation technique
- `reports/` : rapports JSON generes par les scripts
- `firmware/` : manifestes et images locales pour la preparation de flash

## Utilisation

Lancer l’audit principal depuis la racine du projet :

```bash
python3 scripts/audit_android.py
```

Le script :

- detecte les appareils adb connectes
- signale les appareils non autorises
- collecte des informations systeme utiles
- genere un rapport JSON dans `reports/latest_audit.json`

Pour auditer un appareil precis :

```bash
python3 scripts/audit_android.py --serial NUMERO_DE_SERIE
```

## Flash securise

Un second script prepare un plan de flash fastboot avec validation stricte du produit cible :

```bash
python3 scripts/flash_android.py firmware/manifest.example.json
```

Le script est en simulation par defaut et bloque les incompatibilites de produit.
