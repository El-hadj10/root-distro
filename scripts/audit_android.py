#!/usr/bin/env python3
"""
Script d’audit Android : collecte d’informations système via adb
"""
import subprocess

def run_adb_command(cmd):
    try:
        result = subprocess.run(["adb"] + cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Erreur: {e}"

def main():
    print("=== Audit Android (adb) ===")
    print("Appareils connectés :")
    print(run_adb_command(["devices"]))
    print("\nVersion Android :")
    print(run_adb_command(["shell", "getprop", "ro.build.version.release"]))
    print("\nBootloader :")
    print(run_adb_command(["shell", "getprop", "ro.bootloader"]))
    print("\nRoot détecté :")
    print(run_adb_command(["shell", "which", "su"]))

if __name__ == "__main__":
    main()
