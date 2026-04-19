#!/usr/bin/env python3
"""Script d’audit Android via adb."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
DEFAULT_REPORT_PATH = REPORTS_DIR / "latest_audit.json"

ANDROID_PROPERTIES = {
    "android_version": ["shell", "getprop", "ro.build.version.release"],
    "sdk_version": ["shell", "getprop", "ro.build.version.sdk"],
    "device_model": ["shell", "getprop", "ro.product.model"],
    "device_brand": ["shell", "getprop", "ro.product.brand"],
    "device_name": ["shell", "getprop", "ro.product.device"],
    "build_fingerprint": ["shell", "getprop", "ro.build.fingerprint"],
    "bootloader": ["shell", "getprop", "ro.bootloader"],
    "kernel": ["shell", "uname", "-r"],
    "selinux": ["shell", "getenforce"],
}


def run_adb_command(cmd):
    result = subprocess.run(
        ["adb"] + cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode,
    }


def get_connected_devices():
    result = run_adb_command(["devices"])
    if not result["ok"]:
        return [], result

    devices = []
    for line in result["stdout"].splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        serial, status = line.split(maxsplit=1)
        devices.append({"serial": serial, "status": status})
    return devices, result


def detect_root_status():
    result = run_adb_command(["shell", "which", "su"])
    if result["ok"] and result["stdout"]:
        return {"detected": True, "binary_path": result["stdout"]}
    return {"detected": False, "binary_path": None}


def collect_device_report(serial=None):
    devices, devices_result = get_connected_devices()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "adb_devices_output": devices_result["stdout"],
        "devices": devices,
        "target_serial": serial,
        "status": "unknown",
        "details": {},
        "errors": [],
    }

    if not devices:
        report["status"] = "no_device"
        report["errors"].append("Aucun appareil Android detecte par adb.")
        return report

    unauthorized_devices = [device for device in devices if device["status"] == "unauthorized"]
    if unauthorized_devices:
        report["status"] = "unauthorized"
        report["errors"].append(
            "Un appareil est detecte mais le debogage USB n'est pas autorise."
        )
        return report

    target_device = None
    if serial:
        for device in devices:
            if device["serial"] == serial:
                target_device = device
                break
        if target_device is None:
            report["status"] = "serial_not_found"
            report["errors"].append(f"Le numero de serie {serial} est introuvable.")
            return report
    else:
        target_device = devices[0]

    report["target_serial"] = target_device["serial"]
    report["status"] = "ok"

    adb_prefix = ["-s", target_device["serial"]]
    for key, command in ANDROID_PROPERTIES.items():
        result = run_adb_command(adb_prefix + command)
        if result["ok"]:
            report["details"][key] = result["stdout"]
        else:
            report["details"][key] = None
            report["errors"].append(
                f"Impossible de recuperer {key}: {result['stderr'] or result['stdout']}"
            )

    report["details"]["root_status"] = detect_root_status()
    return report


def print_report(report):
    print("=== Audit Android (adb) ===")
    print("Appareils connectes :")
    print(report["adb_devices_output"] or "Aucune sortie adb.")

    if report["status"] != "ok":
        print("\nEtat :", report["status"])
        for error in report["errors"]:
            print("-", error)
        return

    details = report["details"]
    print("\nNumero de serie :")
    print(report["target_serial"])
    print("\nVersion Android :")
    print(details.get("android_version") or "Indisponible")
    print("\nVersion SDK :")
    print(details.get("sdk_version") or "Indisponible")
    print("\nModele :")
    print(details.get("device_model") or "Indisponible")
    print("\nMarque :")
    print(details.get("device_brand") or "Indisponible")
    print("\nNom produit :")
    print(details.get("device_name") or "Indisponible")
    print("\nBootloader :")
    print(details.get("bootloader") or "Indisponible")
    print("\nKernel :")
    print(details.get("kernel") or "Indisponible")
    print("\nSELinux :")
    print(details.get("selinux") or "Indisponible")
    print("\nRoot detecte :")
    print("Oui" if details["root_status"]["detected"] else "Non")
    if details["root_status"]["binary_path"]:
        print(details["root_status"]["binary_path"])

    if report["errors"]:
        print("\nAvertissements :")
        for error in report["errors"]:
            print("-", error)


def save_report(report, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Audit Android via adb")
    parser.add_argument(
        "--serial",
        help="Numero de serie adb de l'appareil a auditer",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT_PATH),
        help="Chemin du rapport JSON a generer",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    report = collect_device_report(serial=args.serial)
    print_report(report)
    save_report(report, Path(args.output))
    print("\nRapport JSON enregistre dans :")
    print(Path(args.output))


if __name__ == "__main__":
    main()
