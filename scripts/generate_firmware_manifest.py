#!/usr/bin/env python3
"""Genere un manifeste firmware a partir d'un rapport d'audit existant."""

import argparse
import json
from pathlib import Path


DEFAULT_PARTITIONS = ["boot", "vendor_boot", "recovery"]


def load_report(report_path):
    return json.loads(report_path.read_text(encoding="utf-8"))


def infer_device(report):
    details = report.get("details", {})
    product = details.get("product") or details.get("device_name")
    model = details.get("device_model")
    brand = details.get("device_brand")
    serial = report.get("target_serial") or details.get("serialno")
    return {
        "brand": brand,
        "model": model,
        "product": product,
        "serial": serial,
    }


def build_manifest(report, image_dir, partitions, manifest_name=None):
    device = infer_device(report)
    if not device["product"]:
        raise ValueError("Impossible d'inferer le produit depuis le rapport fourni.")

    bundle_name = manifest_name or " ".join(
        part for part in [device.get("brand"), device.get("model"), "Recovery Bundle"] if part
    )
    images = []
    for partition in partitions:
        images.append(
            {
                "partition": partition,
                "file": f"{image_dir}/{partition}.img",
                "critical": True,
            }
        )

    return {
        "name": bundle_name,
        "device": {
            "brand": device.get("brand"),
            "model": device.get("model"),
            "product": device.get("product"),
        },
        "source_report": report.get("generated_at"),
        "target_serial": device.get("serial"),
        "images": images,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Generateur de manifeste firmware")
    parser.add_argument("report", help="Chemin vers un rapport d'audit JSON")
    parser.add_argument(
        "--output",
        default="firmware/generated_manifest.json",
        help="Chemin du manifeste JSON a generer",
    )
    parser.add_argument(
        "--image-dir",
        default="images",
        help="Chemin relatif vers les images dans le bundle firmware",
    )
    parser.add_argument(
        "--partitions",
        nargs="+",
        default=DEFAULT_PARTITIONS,
        help="Liste des partitions a inclure dans le manifeste",
    )
    parser.add_argument("--name", help="Nom du bundle firmware")
    return parser.parse_args()


def main():
    args = parse_args()
    report_path = Path(args.report).resolve()
    output_path = Path(args.output).resolve()
    manifest = build_manifest(
        load_report(report_path),
        image_dir=args.image_dir,
        partitions=args.partitions,
        manifest_name=args.name,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Manifeste genere :")
    print(output_path)


if __name__ == "__main__":
    main()