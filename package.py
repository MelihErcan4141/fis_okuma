import argparse
import importlib.metadata
import os
import shutil
import subprocess
import sys
from pathlib import Path

from paddlex.utils import deps as paddlex_deps


APP_NAME = "ReceiptReader"
PADDLEX_EXTRAS = ("ocr", "ocr-core")


def dependency_report():
    """Use PaddleX's runtime dependency list and checks as the source of truth."""
    rows = []
    dependency_names = {
        dependency
        for extra in PADDLEX_EXTRAS
        for dependency in paddlex_deps.EXTRAS[extra]
    }

    for dependency in sorted(dependency_names, key=str.casefold):
        version = paddlex_deps.get_dep_version(dependency)
        rows.append(
            (
                dependency,
                paddlex_deps.is_dep_available(dependency),
                version,
            )
        )
    return rows


def print_dependency_report(rows, heading):
    print(f"\n{heading}")
    print("-" * 70)
    for dependency, available, version in rows:
        status = "OK" if available else "MISSING"
        print(f"{dependency:24} {status:8} metadata={version or 'MISSING'}")


def metadata_args(rows):
    missing = [name for name, available, _ in rows if not available]
    if missing:
        raise RuntimeError(
            "Build ortamında PaddleX OCR bağımlılıkları eksik: "
            + ", ".join(missing)
        )

    args = []
    for dependency, _, _ in rows:
        args.extend(("--copy-metadata", dependency))
    return args


def verify_bundled_metadata(app_path, rows):
    contents = app_path / "Contents"
    missing = []
    for dependency, _, _ in rows:
        try:
            distribution = importlib.metadata.distribution(dependency)
        except importlib.metadata.PackageNotFoundError:
            missing.append(dependency)
            continue

        metadata_dir = Path(distribution._path).name
        if not any(contents.rglob(metadata_dir)):
            missing.append(dependency)

    if missing:
        raise RuntimeError(
            "Build tamamlandı fakat bundle metadata doğrulaması başarısız: "
            + ", ".join(missing)
        )


def fix_macos_openssl(app_path, openssl_prefix):
    frameworks = app_path / "Contents" / "Frameworks"
    cv2_dylibs = frameworks / "cv2" / ".dylibs"
    openssl_lib = openssl_prefix / "lib"

    for filename in ("libssl.3.dylib", "libcrypto.3.dylib"):
        source = openssl_lib / filename
        target = cv2_dylibs / filename
        if not source.is_file():
            raise RuntimeError(f"OpenSSL bulunamadı: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or target.exists():
            target.unlink()
        shutil.copy2(source, target)
        print(f"OpenSSL kütüphanesi değiştirildi: {target}")

    # Bazı wheel dosyaları salt-okunur gelir; xattr temizliği yazma izni ister.
    subprocess.run(("chmod", "-R", "u+w", str(app_path)), check=True)
    # ZIP/Finder kaynaklı resource-fork attribute'ları codesign'ı engeller.
    subprocess.run(("xattr", "-cr", str(app_path)), check=True)
    subprocess.run(
        ("codesign", "--force", "--deep", "--sign", "-", str(app_path)),
        check=True,
    )
    subprocess.run(("codesign", "--verify", "--deep", "--strict", str(app_path)), check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument(
        "--openssl-prefix",
        type=Path,
        default=Path("/opt/homebrew/opt/openssl@3"),
    )
    args = parser.parse_args()

    rows = dependency_report()
    print_dependency_report(rows, "PaddleX OCR build ortamı bağımlılık raporu")

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--windowed",
        "--name",
        APP_NAME,
        "--paths",
        "src",
        "--collect-data",
        "paddlex",
        "--collect-data",
        "paddleocr",
        "--collect-binaries",
        "paddle",
        *metadata_args(rows),
        args.file,
    ]
    build_environment = os.environ.copy()
    build_environment["PYINSTALLER_CONFIG_DIR"] = str(
        (Path("build") / "pyinstaller-cache").resolve()
    )
    subprocess.run(command, check=True, env=build_environment)

    app_path = Path("dist") / f"{APP_NAME}.app"
    verify_bundled_metadata(app_path, rows)

    if sys.platform == "darwin":
        fix_macos_openssl(app_path, args.openssl_prefix)

    print_dependency_report(rows, "Bundle'a kopyalanan PaddleX OCR metadata'ları")
    print(f"\nBuild tamamlandı: {app_path}")


if __name__ == "__main__":
    main()
