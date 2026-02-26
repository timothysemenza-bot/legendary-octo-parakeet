#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def account_tokens(name: str):
    stop = {
        "services",
        "service",
        "security",
        "group",
        "corporation",
        "corp",
        "inc",
        "llc",
        "co",
        "company",
        "north",
        "america",
        "us",
    }
    parts = [p for p in norm(name).split() if p and p not in stop]
    # Keep only meaningful tokens.
    return [p for p in parts if len(p) >= 4]


def pick(row: dict, *keys):
    for k in keys:
        if k in row and row[k]:
            return row[k]
    return ""


def load_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: python crossref-linkedin-connections.py <target_accounts.csv> <linkedin_connections.csv> <output.csv>"
        )
        sys.exit(1)

    target_path = Path(sys.argv[1])
    conn_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    targets = load_csv(target_path)
    conns = load_csv(conn_path)

    for t in targets:
        t["linkedin_match_count"] = "0"
        t["linkedin_matches"] = ""
        t["linkedin_warm_path"] = "No clear match"

        name = t.get("account_name", "")
        tokens = account_tokens(name)
        if not tokens:
            continue

        matches = []
        for c in conns:
            company = pick(c, "Company", "Company Name", "company", "company_name")
            title = pick(c, "Position", "Title", "position", "title")
            first = pick(c, "First Name", "first_name", "FirstName")
            last = pick(c, "Last Name", "last_name", "LastName")

            hay = norm(f"{company} {title}")
            score = sum(1 for tok in tokens if tok in hay)
            if score >= 1:
                full_name = f"{first} {last}".strip()
                desc = " | ".join(
                    x for x in [full_name, company.strip(), title.strip()] if x
                )
                matches.append((score, desc))

        matches.sort(key=lambda x: (-x[0], x[1]))
        if matches:
            top = [m[1] for m in matches[:5]]
            t["linkedin_match_count"] = str(len(matches))
            t["linkedin_matches"] = " || ".join(top)
            t["linkedin_warm_path"] = (
                "Direct/near-direct path available"
                if len(matches) >= 2
                else "Single potential path"
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(targets[0].keys()) if targets else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(targets)

    print(str(out_path))


if __name__ == "__main__":
    main()

