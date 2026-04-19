#!/usr/bin/env python3
"""Planifie et execute une sauvegarde en lecture seule de partitions Android."""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "backups"


def run_adb_command(args):
    result = subprocess.run(
        ["adb"] + args,
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


def resolve_target_device(serial=None):
    devices, result = get_connected_devices()
    if not devices:
        raise RuntimeError(result["stderr"] or "Aucun appareil adb detecte.")

    authorized = [device for device in devices if device["status"] == "device"]
    if not authorized:
        raise RuntimeError("Aucun appareil adb autorise n'est disponible.")

    if serial:
        for device in authorized:
            if device["serial"] == serial:
                return device
        raise RuntimeError(f"Le numero de serie adb {serial} est introuvable.")

    if len(authorized) > 1:
        raise RuntimeError("Plusieurs appareils adb detectes. Utilisez --serial.")
    return authorized[0]


def load_plan(plan_path):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if "partitions" not in plan or not isinstance(plan["partitions"], list):
        raise ValueError("Le plan de sauvegarde doit contenir une liste 'partitions'.")
    return plan


def get_device_properties(serial):
    values = {}
    mapping = {
        "brand": "ro.product.brand",
        "model": "ro.product.model",
        "product": "ro.product.device",
    }
    for key, prop in mapping.items():
        result = run_adb_command(["-s", serial, "shell", "getprop", prop])
        values[key] = result["stdout"] if result["ok"] else None
    return values


def build_backup_plan(plan_path, serial=None):
    plan = load_plan(plan_path)
    device = resolve_target_device(serial)
    properties = get_device_properties(device["serial"])
    expected = plan.get("device", {})
    compatibility_errors = []
    for key in ["brand", "model", "product"]:
        expected_value = expected.get(key)
        actual_value = properties.get(key)
        if expected_value and actual_value and expected_value != actual_value:
            compatibility_errors.append(
                f"{key} incompatible: attendu {expected_value}, detecte {actual_value}."
            )

    resolved = []
    for partition in plan["partitions"]:
        resolved.append(
            {
                "name": partition["name"],
                "source": partition["source"],
                "method": partition.get("method", "adb_exec_out_dd"),
                "optional": partition.get("optional", False),
            }
        )

    return {
        "name": plan.get("name", "Backup plan"),
        "serial": device["serial"],
        "device": properties,
        "compatibility_errors": compatibility_errors,
        "partitions": resolved,
    }


def has_root_access(serial):
    result = run_adb_command(["-s", serial, "shell", "su", "-c", "id -u"])
    return result["ok"] and result["stdout"].strip() == "0"


def backup_partition(serial, partition, output_file):
    if partition["method"] != "adb_exec_out_dd":
        raise RuntimeError(f"Methode non supportee: {partition['method']}")

    command = [
        "adb",
        "-s",
        serial,
        "exec-out",
        "su",
        "-c",
        f"dd if={partition['source']} bs=4M",
    ]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("wb") as stream:
        process = subprocess.run(command, stdout=stream, stderr=subprocess.PIPE, check=False)
    if process.returncode != 0:
        raise RuntimeError(
            process.stderr.decode("utf-8", errors="replace").strip() or "Echec de sauvegarde."
        )


def print_plan(plan):
    print("=== Plan de sauvegarde des partitions ===")
    print("Nom :", plan["name"])
    print("Numero de serie :", plan["serial"])
    print("Appareil :", " / ".join(filter(None, [plan["device"].get("brand"), plan["device"].get("model"), plan["device"].get("product")])))
    print("\nPartitions :")
    for partition in plan["partitions"]:
        print(f"- {partition['name']} <- {partition['source']} ({partition['method']})")

    if plan["compatibility_errors"]:
        print("\nErreurs de compatibilite :")
        for error in plan["compatibility_errors"]:
            print("-", error)


def parse_args():
    parser = argparse.ArgumentParser(description="Sauvegarde en lecture seule de partitions Android")
    parser.add_argument("plan", help="Chemin vers le plan de sauvegarde JSON")
    parser.add_argument("--serial", help="Numero de serie adb cible")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Dossier de sortie des sauvegardes",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute la sauvegarde au lieu d'afficher seulement le plan",
    )
    parser.add_argument(
        "--i-understand-risks",
        action="store_true",
        help="Confirmation explicite requise pour executer une sauvegarde de partitions",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    plan_path = Path(args.plan).resolve()
    backup_plan = build_backup_plan(plan_path, serial=args.serial)
    print_plan(backup_plan)

    if not args.execute:
        print("\nMode simulation: aucune sauvegarde n'a ete executee.")
        return

    if backup_plan["compatibility_errors"]:
        print("\nExecution refusee: le plan n'est pas compatible avec l'appareil cible.")
        sys.exit(2)

    if not args.i_understand_risks:
        print("\nExecution refusee: ajoutez --i-understand-risks pour confirmer.")
        sys.exit(2)

    if not has_root_access(backup_plan["serial"]):
        raise RuntimeError("L'appareil ne permet pas la lecture root via su pour cette sauvegarde.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_root = Path(args.output_dir).resolve() / backup_plan["serial"] / timestamp
    for partition in backup_plan["partitions"]:
        output_file = output_root / f"{partition['name']}.img"
        backup_partition(backup_plan["serial"], partition, output_file)
        print(f"Sauvegarde terminee : {output_file}")


if __name__ == "__main__":
    main()