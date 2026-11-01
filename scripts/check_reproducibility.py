import hashlib
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "output"

FILES_TO_CHECK = [
    "customers.csv",
    "products.csv",
    "categories.csv",
    "orders.csv",
    "complaints.csv",
    "assignments.csv",
    "sla_clocks.csv",
    "complaint_messages.csv",
    "status_events.csv",
    "resolutions.csv",
    "surveys.csv",
]


def file_checksum(path):
    sha256 = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_checksums():
    return {
        filename: file_checksum(OUTPUT_DIR / filename)
        for filename in FILES_TO_CHECK
    }


def main():
    print("=" * 60)
    print("REPRODUCIBILITY CHECK")
    print("=" * 60)

    print("\nGenerating dataset for run 1...")
    subprocess.run(
        [sys.executable, "-m", "src.generator.generate"],
        cwd=BASE_DIR,
        check=True,
    )

    checksums_run_1 = get_checksums()

    print("\nGenerating dataset for run 2...")
    subprocess.run(
        [sys.executable, "-m", "src.generator.generate"],
        cwd=BASE_DIR,
        check=True,
    )

    checksums_run_2 = get_checksums()

    print("\nComparing checksums...")

    all_match = True

    for filename in FILES_TO_CHECK:
        match = (
            checksums_run_1[filename]
            == checksums_run_2[filename]
        )

        status = "MATCH" if match else "DIFFERENT"

        print(f"{filename:<30} {status}")

        if not match:
            all_match = False

    print("\n" + "=" * 60)

    if all_match:
        print("REPRODUCIBILITY CHECK PASSED")
        print("Same seed produced identical datasets.")
    else:
        print("REPRODUCIBILITY CHECK FAILED")
        print("Dataset changed between runs.")

        raise SystemExit(1)


if __name__ == "__main__":
    main()