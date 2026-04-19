#!/usr/bin/env python3
"""Prepare et execute un flash Android via fastboot avec garde-fous."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRITICAL_PARTITIONS = {
    "abl",
    "boot",
    "bootloader",
    "dtbo",
    "init_boot",
    "modem",
    "recovery",
    "super",
    "vbmeta",
    "vbmeta_system",
    "vendor_boot",
}


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


def get_connected_fastboot_devices():
    result = run_fastboot_command(["devices"])
    if not result["ok"]:
        return [], result

    devices = []
    for line in result["stdout"].splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            devices.append({"serial": parts[0], "mode": parts[1]})
    return devices, result


def get_fastboot_var(serial, variable):
    result = run_fastboot_command(["-s", serial, "getvar", variable])
    combined = "\n".join(part for part in [result["stdout"], result["stderr"]] if part)
    for line in combined.splitlines():
        normalized = line.strip().lower()
        prefix = f"{variable.lower()}:"
        if normalized.startswith(prefix):
            return line.split(":", 1)[1].strip(), result
    return None, result


def load_manifest(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required_keys = ["name", "device", "images"]
    missing = [key for key in required_keys if key not in manifest]
    if missing:
        raise ValueError(f"Manifest incomplet, champs manquants: {', '.join(missing)}")
    if not isinstance(manifest["images"], list) or not manifest["images"]:
        raise ValueError("Le manifeste doit contenir une liste d'images non vide.")
    return manifest


def validate_images(manifest_path, manifest, strict_files):
    warnings = []
    resolved_images = []
    for image in manifest["images"]:
        if "partition" not in image or "file" not in image:
            warnings.append("Chaque image doit definir 'partition' et 'file'.")
            continue

        image_path = (manifest_path.parent / image["file"]).resolve()
        resolved_images.append(
            {
                "partition": image["partition"],
                "file": str(image_path),
                "exists": image_path.exists(),
                "critical": image.get("critical", image["partition"] in CRITICAL_PARTITIONS),
                "optional": image.get("optional", False),
            }
        )

        if not image_path.exists():
            message = f"Fichier introuvable pour {image['partition']}: {image_path}"
            if strict_files and not image.get("optional", False):
                raise RuntimeError(message)
            warnings.append(message)

    return resolved_images, warnings


def resolve_target_device(requested_serial=None):
    devices, result = get_connected_fastboot_devices()
    if not devices:
        raise RuntimeError(result["stderr"] or "Aucun appareil fastboot detecte.")

    if requested_serial:
        for device in devices:
            if device["serial"] == requested_serial:
                return device
        raise RuntimeError(f"Le numero de serie fastboot {requested_serial} est introuvable.")

    if len(devices) > 1:
        raise RuntimeError("Plusieurs appareils fastboot detectes. Utilisez --serial.")
    return devices[0]


def build_flash_plan(manifest_path, serial=None, require_device=True, strict_files=False):
    manifest = load_manifest(manifest_path)
    images, image_warnings = validate_images(manifest_path, manifest, strict_files=strict_files)

    expected_product = manifest["device"].get("product")
    expected_model = manifest["device"].get("model")
    expected_brand = manifest["device"].get("brand")

    device = None
    product = None
    secure_state = None
    unlocked = None
    compatibility_errors = []

    if require_device:
        device = resolve_target_device(serial)
        product, product_result = get_fastboot_var(device["serial"], "product")
        secure_state, _ = get_fastboot_var(device["serial"], "secure")
        unlocked, _ = get_fastboot_var(device["serial"], "unlocked")

        if not product:
            raise RuntimeError(
                product_result["stderr"] or "Impossible de lire la variable fastboot 'product'."
            )

        if expected_product and product != expected_product:
            compatibility_errors.append(
                f"Produit incompatible: attendu {expected_product}, detecte {product}."
            )

    plan = {
        "manifest_name": manifest["name"],
        "serial": device["serial"] if device else None,
        "product": product,
        "expected_product": expected_product,
        "expected_model": expected_model,
        "expected_brand": expected_brand,
        "secure": secure_state,
        "unlocked": unlocked,
        "images": images,
        "warnings": image_warnings,
        "compatibility_errors": compatibility_errors,
    }
    return plan


def print_plan(plan):
    print("=== Plan de flash Android (fastboot) ===")
    print("Manifeste :", plan["manifest_name"])
    print("Numero de serie :", plan["serial"] or "Non verifie")
    print("Produit detecte :", plan["product"] or "Non verifie")
    if plan["expected_product"]:
        print("Produit attendu :", plan["expected_product"])
    print("Secure :", plan["secure"] or "Indetermine")
    print("Bootloader deverrouille :", plan["unlocked"] or "Indetermine")
    if plan["expected_brand"]:
        print("Marque attendue :", plan["expected_brand"])
    if plan["expected_model"]:
        print("Modele attendu :", plan["expected_model"])

    print("\nImages preparees :")
    for image in plan["images"]:
        critical_flag = "critique" if image["critical"] else "standard"
        file_state = "present" if image["exists"] else "absent"
        print(f"- {image['partition']} <- {image['file']} ({critical_flag}, {file_state})")

    if plan["warnings"]:
        print("\nAvertissements :")
        for warning in plan["warnings"]:
            print("-", warning)

    if plan["compatibility_errors"]:
        print("\nErreurs de compatibilite :")
        for error in plan["compatibility_errors"]:
            print("-", error)


def execute_flash_plan(plan, allow_critical):
    if plan["compatibility_errors"]:
        raise RuntimeError("Flash bloque: incompatibilite manifeste/appareil.")

    missing_required = [image for image in plan["images"] if not image["exists"] and not image["optional"]]
    if missing_required:
        raise RuntimeError(
            "Flash bloque: images manquantes: "
            + ", ".join(image["partition"] for image in missing_required)
        )

    if plan["unlocked"] and plan["unlocked"].lower() in {"no", "0", "false"}:
        raise RuntimeError("Flash bloque: bootloader verrouille.")

    executed = []
    for image in plan["images"]:
        if image["critical"] and not allow_critical:
            raise RuntimeError(
                f"Flash bloque: la partition critique {image['partition']} requiert --allow-critical."
            )

        result = run_fastboot_command(
            ["-s", plan["serial"], "flash", image["partition"], image["file"]]
        )
        if not result["ok"]:
            raise RuntimeError(
                f"Echec du flash de {image['partition']}: {result['stderr'] or result['stdout']}"
            )
        executed.append(image["partition"])
    return executed


def parse_args():
    parser = argparse.ArgumentParser(description="Planificateur de flash Android via fastboot")
    parser.add_argument("manifest", help="Chemin vers le manifeste firmware JSON")
    parser.add_argument("--serial", help="Numero de serie fastboot cible")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute le flash au lieu d'afficher uniquement le plan",
    )
    parser.add_argument(
        "--allow-critical",
        action="store_true",
        help="Autorise le flash des partitions critiques",
    )
    parser.add_argument(
        "--i-understand-risks",
        action="store_true",
        help="Confirmation explicite requise pour un flash reel",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Valide uniquement le manifeste et les chemins de fichiers, sans appareil fastboot",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    plan = build_flash_plan(
        manifest_path,
        serial=args.serial,
        require_device=not args.manifest_only,
        strict_files=args.execute,
    )
    print_plan(plan)

    if args.manifest_only:
        print("\nValidation du manifeste terminee sans appareil fastboot.")
        return

    if not args.execute:
        print("\nMode simulation: aucun flash n'a ete execute.")
        return

    if not args.i_understand_risks:
        print("\nExecution refusee: ajoutez --i-understand-risks pour confirmer.")
        sys.exit(2)

    executed = execute_flash_plan(plan, allow_critical=args.allow_critical)
    print("\nPartitions flashees :")
    for partition in executed:
        print("-", partition)


if __name__ == "__main__":
    main()
