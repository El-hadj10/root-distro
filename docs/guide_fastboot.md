# Guide d'audit fastboot

Ce guide couvre l'audit d'un appareil deja demarre en mode bootloader ou fastboot.

## Commande principale

```bash
python3 scripts/audit_fastboot.py
```

## Ce que le script recupere

- la liste des appareils fastboot detectes
- le produit expose par le bootloader
- l'etat secure et unlocked
- la version du bootloader et du baseband
- le slot courant si l'information est disponible

## Sortie

Le rapport est ecrit dans `reports/latest_fastboot_audit.json`.

## Cas utiles

- verifier qu'un appareil est bien en fastboot avant un reflash
- recuperer le `product` exact pour comparer avec un manifeste firmware
- documenter l'etat du bootloader avant intervention
