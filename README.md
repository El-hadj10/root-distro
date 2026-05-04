<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d0d0d,100:e63946&height=200&section=header&text=root-distro&fontSize=52&fontColor=ffffff&fontAlignY=38&desc=Android+Audit+%26+Firmware+Toolkit+%7C+adb+%C2%B7+fastboot+%C2%B7+Python&descAlignY=58&descSize=16" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-3572A5?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Android-adb%20%7C%20fastboot-3DDC84?style=for-the-badge&logo=android&logoColor=white" />
  <img src="https://img.shields.io/badge/Usage-Audit%20%26%20Diagnostic-e63946?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Licence-MIT-lightgrey?style=for-the-badge" />
</p>

---

## Objectif

**root-distro** est un toolkit Python d'audit et de diagnostic Android via `adb` et `fastboot`.

Il collecte des informations systeme sur un appareil connecte, verifie l'etat du bootloader, la presence du root, les partitions disponibles, et genere des rapports JSON exploitables.

> Aucune operation de contournement ou d'elevation de privileges n'est realisee.
> L'outil est concu pour l'audit, le diagnostic et la preparation de flash controlee.

---

## Architecture

\`\`\`
root-distro/
├── scripts/
│   ├── audit_android.py              Audit principal adb (detection, collecte, rapport)
│   ├── audit_fastboot.py             Audit bootloader via fastboot
│   ├── flash_android.py              Plan de flash fastboot (simulation stricte)
│   ├── backup_partitions.py          Plan de sauvegarde des partitions lisibles
│   └── generate_firmware_manifest.py Generation manifeste firmware depuis rapport
├── docs/
│   ├── guide_utilisation.md          Guide d'utilisation general
│   ├── guide_fastboot.md             Guide fastboot & bootloader
│   ├── guide_flash.md                Guide flash securise
│   └── guide_backup.md               Guide backup partitions
├── firmware/                         Manifestes et images pour preparation de flash
├── reports/                          Rapports JSON generes (latest_audit.json, ...)
├── backups/                          Sauvegardes locales avant reflash
└── android-app/                      Application Android complementaire
\`\`\`

---

## Stack technique

| Composant     | Technologie                  |
|---------------|------------------------------|
| Langage       | Python 3                     |
| Interface ADB | `adb` (Android Debug Bridge) |
| Interface BL  | `fastboot`                   |
| Rapports      | JSON                         |
| Documentation | Markdown                     |

---

## Utilisation

### Audit principal (adb)

\`\`\`bash
python3 scripts/audit_android.py
\`\`\`

Detecte les appareils connectes, collecte les infos systeme, genere `reports/latest_audit.json`.

Pour cibler un appareil precis :

\`\`\`bash
python3 scripts/audit_android.py --serial NUMERO_DE_SERIE
\`\`\`

### Audit bootloader (fastboot)

\`\`\`bash
python3 scripts/audit_fastboot.py
\`\`\`

### Flash securise (simulation par defaut)

\`\`\`bash
python3 scripts/flash_android.py firmware/manifest.example.json
\`\`\`

Valide l'identite du produit cible avant toute operation — bloque les incompatibilites.

### Generation de manifeste firmware

\`\`\`bash
python3 scripts/generate_firmware_manifest.py reports/latest_audit.json
\`\`\`

### Plan de sauvegarde des partitions

\`\`\`bash
python3 scripts/backup_partitions.py firmware/backup_plan.example.json
\`\`\`

---

## Securite & ethique

- Aucune exploitation de vulnerabilite ni bypass de securite Android
- Toutes les operations de flash sont en mode **simulation** par defaut
- Validation stricte du produit cible avant tout plan de flash
- Concu pour un usage sur ses propres appareils ou avec autorisation explicite

---

## Roadmap

- [ ] Interface CLI interactive (menu guide)
- [ ] Rapport HTML en plus du JSON
- [ ] Detection automatique du modele et du firmware disponible
- [ ] Support multi-appareils simultanees
- [ ] Export des rapports vers un dashboard web

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:e63946,100:0d0d0d&height=120&section=footer" />
</p>

<p align="center">
  Concu par <strong>Nour</strong> &middot; <a href="https://github.com/El-hadj10">El-hadj10</a><br/>
  <em>Full-Stack Developer &amp; Cybersecurity Enthusiast</em>
</p>
