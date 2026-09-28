import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_records(schema_path: Path, dataset_path: Path) -> int:
    schema = load_json(schema_path)
    dataset = load_json(dataset_path)

    validator = Draft202012Validator(schema)
    records = dataset if isinstance(dataset, list) else [dataset]

    failures = 0

    for index, record in enumerate(records, start=1):
        errors = sorted(
            validator.iter_errors(record),
            key=lambda error: list(error.absolute_path),
        )

        family_id = record.get("family_id", f"record_{index}")

        if errors:
            failures += 1
            print(f"FAIL: {family_id}")
            for error in errors:
                location = ".".join(str(part) for part in error.absolute_path)
                print(f"  {location or '<root>'}: {error.message}")
        else:
            print(f"PASS: {family_id}")

    if failures:
        print(f"Validation failed: {failures} record(s) invalid.")
        return 1

    print(f"Validation complete: {len(records)} record(s) passed.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate scenario families against a JSON Schema."
    )
    parser.add_argument("schema", type=Path)
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()

    raise SystemExit(validate_records(args.schema, args.dataset))


if __name__ == "__main__":
    main()
