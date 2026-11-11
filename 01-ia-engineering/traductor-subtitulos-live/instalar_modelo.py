"""Descarga (una sola vez) el paquete de traduccion ingles -> espanol."""

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import argostranslate.package as pkgs
import argostranslate.translate as tr


def main() -> int:
    ya = [p for p in pkgs.get_installed_packages()
          if p.from_code == "en" and p.to_code == "es"]
    if ya:
        print("El paquete en->es ya esta instalado.")
    else:
        print("Actualizando indice de paquetes...")
        pkgs.update_package_index()
        elegido = next(
            p for p in pkgs.get_available_packages()
            if p.from_code == "en" and p.to_code == "es"
        )
        print("Descargando (~100 MB, solo esta vez)...")
        pkgs.install_from_path(elegido.download())
        print("Instalado.")

    print("Prueba:", tr.translate("Hello, how are you?", "en", "es"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
