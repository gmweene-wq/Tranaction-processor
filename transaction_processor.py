#!/usr/bin/env python3

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RECEIVED_PATTERNS = [
    re.compile(r"You have received\s+([\d,]+)\s*RWF\s+from", re.IGNORECASE),
    re.compile(r"\*113\*R\*A bank deposit of\s+([\d,]+)\s*RWF", re.IGNORECASE),
    re.compile(r"\*143\*R\*.*?transaction with amount\s+([\d,]+)\s*RWF", re.IGNORECASE),
    re.compile(r"\bDEPOSIT\s+RWF\s+([\d,]+)", re.IGNORECASE),
]

SENT_PATTERNS = [
    re.compile(r"Your payment of\s+([\d,]+)\s*RWF\s+to", re.IGNORECASE),
    re.compile(r"\*165\*S\*\s*([\d,]+)\s*RWF\s+transferred to", re.IGNORECASE),
    re.compile(r"You have transferred\s+([\d,]+)\s*RWF\s+to", re.IGNORECASE),
    re.compile(r"\*164\*S\*.*?transaction of\s+([\d,]+)\s*RWF\s+by", re.IGNORECASE),
    re.compile(r"Umaze kugura.*?igura\s+([\d,]+)\s*RWF", re.IGNORECASE),
    re.compile(r"withdrawn\s+([\d,]+)\s*RWF\s+from your mobile money account", re.IGNORECASE),
]

# Things to skip: OTPs, reversals, and anything else that doesn't represent a new transaction.
SKIP_PATTERNS = [
    re.compile(r"one-time password", re.IGNORECASE),
    re.compile(r"reversal has been initiated", re.IGNORECASE),
    re.compile(r"has been reversed", re.IGNORECASE),
]


def clean_amount(raw: str) -> int:
    return int(raw.replace(",", "").replace(" ", "").strip())


def classify(body: str):
    if not body:
        return None, None

    for pat in SKIP_PATTERNS:
        if pat.search(body):
            return None, None

    for pat in RECEIVED_PATTERNS:
        m = pat.search(body)
        if m:
            return "received", clean_amount(m.group(1))

    for pat in SENT_PATTERNS:
        m = pat.search(body)
        if m:
            return "sent", clean_amount(m.group(1))

    return None, None


def parse_file(xml_path: Path):
    sent, received = [], []
    skipped = 0


    for _event, elem in ET.iterparse(str(xml_path), events=("end",)):
        if elem.tag != "sms":
            continue

        body = elem.get("body", "") or ""
        readable_date = elem.get("readable_date", "")
        category, amount = classify(body)

        if category == "sent":
            sent.append({"amount": amount, "date": readable_date})
        elif category == "received":
            received.append({"amount": amount, "date": readable_date})
        else:
            skipped += 1

        elem.clear()

    return sent, received, skipped


def print_summary(sent, received, skipped, input_path):
    sent_total = sum(r["amount"] for r in sent)
    recieved_total = sum(r["amount"] for r in received)
    total_count = len(sent) + len(received)
    grand_total = sent_total + recieved_total

    
    print("            TRANSACTION SUMMARY REPORT  \n            ")

    print(f"  Source file          : {input_path}")
    print("----------------------------------------------------")
    print(f"  Money SENT     count : {len(sent):,}")
    print(f"  Money SENT     total : {sent_total:,} RWF")
    print("----------------------------------------------------")
    print(f"  Money RECEIVED count : {len(received):,}")
    print(f"  Money RECEIVED total : {recieved_total:,} RWF")
    print("----------------------------------------------------")
    print(f"  TOTAL transactions   : {total_count:,}")
    print(f"  GRAND TOTAL (sent+rx): {grand_total:,} RWF")
    print(f"  Skipped (OTPs, reversals, etc.)  : {skipped:,}")
    


def print_list(records, label):
    print(f"--- {label} ({len(records)} transactions) ---")
    for r in records:
        print(f"  {r['amount']:>10,} RWF  |  {r['date']}")
    total = sum(r["amount"] for r in records)
    print(f"  {'-' * 40}")
    print(f"  {label} TOTAL: {total:,} RWF")
    print()


def main():
    # Parse arguments: positional input.xml, optional --mode flag
    args = sys.argv[1:]
    mode = "summary"
    positional = []
    i = 0
    while i < len(args):
        if args[i] == "--mode" and i + 1 < len(args):
            mode = args[i + 1]
            i += 2
        else:
            positional.append(args[i])
            i += 1

    input_path = Path(positional[0]) if positional else Path("modified_sms_v2.xml")

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    sent, received, skipped = parse_file(input_path)

    if mode == "counts":
        # Machine-readable single line for the shell script.
        sent_total = sum(r["amount"] for r in sent)
        recv_total = sum(r["amount"] for r in received)
        print(f"{len(sent)} {len(received)} {sent_total} {recv_total}")
    elif mode == "sent":
        print_list(sent, "SENT")
    elif mode == "received":
        print_list(received, "RECEIVED")
    elif mode == "all":
        print_list(sent, "SENT")
        print_list(received, "RECEIVED")
        print_summary(sent, received, skipped, input_path)
    else:  # summary (default)
        print_summary(sent, received, skipped, input_path)


if __name__ == "__main__":
    main()
