import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Freeze a validated pilot dataset and write SHA-256 fingerprints."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--version", default="v0.1")
    parser.add_argument("--expected-families", type=int, default=10)
    parser.add_argument("--conditions-per-family", type=int, default=4)
    args = parser.parse_args()

    files = sorted(args.source_dir.glob(f"{args.prefix}_*.json"))
    if len(files) != args.expected_families:
        raise SystemExit(
            f"Expected {args.expected_families} families, found {len(files)}."
        )

    frozen_root = args.source_dir.parent / "frozen" / f"pilot_{args.version}"
    if frozen_root.exists():
        raise SystemExit(
            f"Refusing to overwrite existing freeze: {frozen_root}\n"
            "Create a new version instead of modifying a frozen dataset."
        )

    frozen_root.mkdir(parents=True)

    manifest_files = []
    combined = hashlib.sha256()

    for src in files:
        dst = frozen_root / src.name
        shutil.copy2(src, dst)
        digest = sha256_file(dst)

        manifest_files.append({
            "file": src.name,
            "sha256": digest,
        })

        combined.update(src.name.encode("utf-8"))
        combined.update(b"\0")
        combined.update(digest.encode("ascii"))
        combined.update(b"\n")

    manifest = {
        "freeze_version": args.version,
        "project": args.project,
        "prefix": args.prefix,
        "family_count": len(files),
        "conditions_per_family": args.conditions_per_family,
        "message_count": len(files) * args.conditions_per_family,
        "source_directory": str(args.source_dir),
        "frozen_directory": str(frozen_root),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "files": manifest_files,
        "dataset_sha256": combined.hexdigest(),
        "immutability_note": (
            "This directory is a frozen research artifact. "
            "Do not modify files in place; create a new dataset version instead."
        ),
    }

    manifest_path = frozen_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Frozen dataset: {frozen_root}")
    print(f"Families: {manifest['family_count']}")
    print(f"Messages: {manifest['message_count']}")
    print(f"Dataset SHA-256: {manifest['dataset_sha256']}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
