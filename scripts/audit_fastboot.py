#!/usr/bin/env python3
"""Audit fastboot en lecture seule avec export JSON."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
DEFAULT_REPORT_PATH = REPORTS_DIR / "latest_fastboot_audit.json"
FASTBOOT_VARS = [
    "product",
    "serialno",
    "secure",
    "unlocked",
    "slot-count",
    "current-slot",
    "version-bootloader",
    "version-baseband",
    "is-userspace",
]


def run_fastboot_command(args):
    try:
        result = subprocess.run(
            ["fastboot"] + args,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "stdout": "",
            "stderr": "La commande fastboot est introuvable. Installez android-tools-fastboot.",
            "returncode": 127,
        }
    return {
        "ok": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode,
    }


def get_connected_devices():
    result = run_fastboot_command(["devices"])
    if not result["ok"]:
        return [], result

    devices = []
    for line in result["stdout"].splitlines():
        parts = line.split()
        if len(parts) >= 2:
            devices.append({"serial": parts[0], "mode": parts[1]})
    return devices, result


def parse_fastboot_value(variable, result):
    combined = "\n".join(part for part in [result["stdout"], result["stderr"]] if part)
    prefix = f"{variable.lower()}:"
    for line in combined.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(prefix):
            return stripped.split(":", 1)[1].strip()
    return None


def collect_fastboot_report(serial=None):
    devices, devices_result = get_connected_devices()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fastboot_devices_output": devices_result["stdout"],
        "devices": devices,
        "target_serial": serial,
        "status": "unknown",
        "details": {},
        "errors": [],
    }

    if not devices:
        report["status"] = "no_device"
        report["errors"].append("Aucun appareil fastboot detecte.")
        return report

    target = None
    if serial:
        for device in devices:
            if device["serial"] == serial:
                target = device
                break
        if target is None:
            report["status"] = "serial_not_found"
            report["errors"].append(f"Le numero de serie fastboot {serial} est introuvable.")
            return report
    else:
        if len(devices) > 1:
            report["status"] = "multiple_devices"
            report["errors"].append("Plusieurs appareils fastboot detectes. Utilisez --serial.")
            return report
        target = devices[0]

    report["status"] = "ok"
    report["target_serial"] = target["serial"]
    report["details"]["mode"] = target["mode"]

    for variable in FASTBOOT_VARS:
        result = run_fastboot_command(["-s", target["serial"], "getvar", variable])
        value = parse_fastboot_value(variable, result)
        report["details"][variable.replace("-", "_")] = value
        if value is None:
            report["errors"].append(
                f"Impossible de lire {variable}: {result['stderr'] or result['stdout']}"
            )
    return report


def save_report(report, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def print_report(report):
    print("=== Audit Fastboot ===")
    print(report["fastboot_devices_output"] or "Aucune sortie fastboot.")

    if report["status"] != "ok":
        print("\nEtat :", report["status"])
        for error in report["errors"]:
            print("-", error)
        return

    details = report["details"]
    print("\nNumero de serie :")
    print(report["target_serial"])
    print("\nProduit :")
    print(details.get("product") or "Indisponible")
    print("\nBootloader version :")
    print(details.get("version_bootloader") or "Indisponible")
    print("\nBaseband version :")
    print(details.get("version_baseband") or "Indisponible")
    print("\nBootloader deverrouille :")
    print(details.get("unlocked") or "Indetermine")
    print("\nSecure :")
    print(details.get("secure") or "Indetermine")
    print("\nSlot courant :")
    print(details.get("current_slot") or "Indisponible")

    if report["errors"]:
        print("\nAvertissements :")
        for error in report["errors"]:
            print("-", error)


def parse_args():
    parser = argparse.ArgumentParser(description="Audit fastboot Android")
    parser.add_argument("--serial", help="Numero de serie fastboot cible")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT_PATH),
        help="Chemin du rapport JSON a generer",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    report = collect_fastboot_report(serial=args.serial)
    print_report(report)
    save_report(report, Path(args.output))
    print("\nRapport JSON enregistre dans :")
    print(Path(args.output))


if __name__ == "__main__":
    main()