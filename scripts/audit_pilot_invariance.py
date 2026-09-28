import argparse
import csv
import json
import re
from pathlib import Path

EXPECTED_CONDITIONS = {
    "DC": ("direct", "conversational"),
    "DI": ("direct", "institutional"),
    "MC": ("mitigated", "conversational"),
    "MI": ("mitigated", "institutional"),
}

WEEKDAYS = {
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday", "today", "tomorrow",
}

HIGH_RISK_MARKERS = {
    "authority": {"manager", "policy", "procedure", "official", "authorized", "required", "mandatory"},
    "sanction": {"penalty", "disciplinary", "warning", "sanction", "consequence", "escalate", "escalation"},
    "urgency": {"urgent", "urgently", "immediately", "asap", "critical", "emergency"},
    "evidence": {"evidence", "proof", "documented", "documentation", "data", "calculation"},
}

NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b", re.I)
WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def tokens(text: str):
    return [x.lower() for x in WORD_RE.findall(text)]

def numbers(text: str):
    return sorted(NUMBER_RE.findall(text))

def weekdays(text: str):
    t = set(tokens(text))
    return sorted(t & WEEKDAYS)

def marker_hits(text: str):
    t = set(tokens(text))
    return {
        category: sorted(t & words)
        for category, words in HIGH_RISK_MARKERS.items()
        if t & words
    }

def main():
    parser = argparse.ArgumentParser(
        description="Audit pilot scenario families for possible semantic-invariance confounds."
    )
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("prefix")
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()

    files = sorted(args.data_dir.glob(f"{args.prefix}_*.json"))
    if not files:
        raise SystemExit("No matching scenario files found.")

    rows = []
    family_flags = []

    for path in files:
        record = load(path)
        fid = record["family_id"]
        conditions = record["conditions"]

        flags = []

        if set(conditions) != set(EXPECTED_CONDITIONS):
            flags.append("condition_set")

        for label, (expected_directness, expected_register) in EXPECTED_CONDITIONS.items():
            c = conditions.get(label, {})
            if c.get("directness") != expected_directness:
                flags.append(f"{label}_directness")
            if c.get("register") != expected_register:
                flags.append(f"{label}_register")

        msgs = {label: conditions[label]["message"] for label in EXPECTED_CONDITIONS}

        number_sets = {label: numbers(msg) for label, msg in msgs.items()}
        if len({tuple(v) for v in number_sets.values()}) > 1:
            flags.append("numeric_asymmetry")

        weekday_sets = {label: weekdays(msg) for label, msg in msgs.items()}
        if len({tuple(v) for v in weekday_sets.values()}) > 1:
            flags.append("temporal_asymmetry")

        marker_sets = {label: marker_hits(msg) for label, msg in msgs.items()}
        for category in HIGH_RISK_MARKERS:
            present = {
                label: tuple(marker_sets[label].get(category, []))
                for label in EXPECTED_CONDITIONS
            }
            if len(set(present.values())) > 1:
                flags.append(f"{category}_marker_asymmetry")

        lengths = {label: len(tokens(msg)) for label, msg in msgs.items()}
        min_len = min(lengths.values())
        max_len = max(lengths.values())
        length_ratio = (max_len / min_len) if min_len else 999.0
        if length_ratio > 1.60:
            flags.append("length_ratio_gt_1.60")

        flags = sorted(set(flags))
        family_flags.append((fid, flags))

        for label in ("DC", "DI", "MC", "MI"):
            rows.append({
                "family_id": fid,
                "domain": record["domain"],
                "role_relation": record["role_relation"],
                "condition": label,
                "directness": conditions[label]["directness"],
                "register": conditions[label]["register"],
                "word_count": lengths[label],
                "numbers": "; ".join(number_sets[label]),
                "temporal_tokens": "; ".join(weekday_sets[label]),
                "high_risk_markers": json.dumps(marker_sets[label], ensure_ascii=False),
                "automatic_family_flags": "; ".join(flags),
                "message": msgs[label],
                "manual_semantic_equivalence": "",
                "manual_factual_invariance": "",
                "manual_pragmatic_manipulation_clear": "",
                "manual_confounds_absent": "",
                "manual_notes": "",
            })

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    flagged = [(fid, flags) for fid, flags in family_flags if flags]

    print(f"Families audited: {len(files)}")
    print(f"Condition messages audited: {len(rows)}")
    print(f"Families with automatic review flags: {len(flagged)}")

    for fid, flags in flagged:
        print(f"REVIEW: {fid}: {', '.join(flags)}")

    if not flagged:
        print("Automatic audit: no heuristic flags.")
    print(f"Audit sheet written to: {args.output_csv}")

if __name__ == "__main__":
    main()
