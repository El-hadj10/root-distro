# Guide de sauvegarde des partitions

Ce flux sert a sauvegarder des partitions lisibles avant un reflash. Il est limite a une lecture locale vers le poste de travail et ne tente aucune ecriture sur l'appareil.

## Limites

- le script reste en simulation par defaut
- l'execution reelle requiert une confirmation explicite
- la lecture de partitions bloc demande souvent un acces root `su` cote appareil
- les sauvegardes generees sont ignorees par Git

## Simulation

```bash
python3 scripts/backup_partitions.py firmware/backup_plan.example.json
```

## Execution reelle

```bash
python3 scripts/backup_partitions.py firmware/backup_plan.example.json --execute --i-understand-risks
```

## Resultat

Les images sont ecrites sous `backups/<serial>/<horodatage>/`.

## Preparation recommandee

- verifier la compatibilite du plan avec un audit adb recent
- limiter la sauvegarde aux partitions necessaires
- tester le plan en simulation avant toute execution reelle
