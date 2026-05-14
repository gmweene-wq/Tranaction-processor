# MoMo SMS Transaction Analyzer

A small Python tool for parsing an **MTN Mobile Money (MoMo)** SMS backup
(XML format) and summarizing it on the terminal. It separates every
transaction into **money sent** and **money received**, then reports the
counts and totals.

Nothing is written to disk — all output goes straight to your terminal.

---

## Files

| File | Purpose |
| --- | --- |
| `transaction_processor.py` | Python parser. Reads the XML, classifies each SMS, prints results. |
| `modified_sms_v2.xml`      | The MoMo SMS backup to analyze (provided separately). |
| `README.md`                | This file. |

---

## Requirements

- **Python 3.7+** (uses only the standard library — no `pip install` needed)
- A POSIX-ish environment (Linux, macOS, or WSL on Windows) — though the
  script also runs fine on plain Windows with Python installed.

---

## Quick start

Put the project files in one folder, alongside your XML backup:

```
my-folder/
├── transaction_processor.py
├── modified_sms_v2.xml
└── README.md
```

Run the script:

```bash
python3 transaction_processor.py
```

That uses the default filename `modified_sms_v2.xml`. To point at a
different file:

```bash
python3 transaction_processor.py /path/to/another_backup.xml
```

---

## Expected output

```
            TRANSACTION SUMMARY REPORT
  Source file          : modified_sms_v2.xml
----------------------------------------------------
  Money SENT     count : 1,366
  Money SENT     total : 16,531,043 RWF
----------------------------------------------------
  Money RECEIVED count : 315
  Money RECEIVED total : 16,435,353 RWF
----------------------------------------------------
  TOTAL transactions   : 1,681
  GRAND TOTAL (sent+rx): 32,966,396 RWF
  Skipped (OTPs etc.)  : 10
```

---

## Run modes

The script supports four different modes via the `--mode` flag:

```bash
# Default — boxed summary report
python3 transaction_processor.py modified_sms_v2.xml

# List every sent transaction with date, then a total
python3 transaction_processor.py modified_sms_v2.xml --mode sent

# List every received transaction with date, then a total
python3 transaction_processor.py modified_sms_v2.xml --mode received

# Both lists followed by the summary
python3 transaction_processor.py modified_sms_v2.xml --mode all

# Machine-readable single line:
#   <sent_count> <received_count> <sent_total> <received_total>
python3 transaction_processor.py modified_sms_v2.xml --mode counts
```

---

## How transactions are classified

Every `<sms>` element's `body` attribute is matched against a list of
regular expressions. The first pattern that matches decides whether the
message is **sent**, **received**, or **skipped**.

### Counted as RECEIVED
- `You have received <amount> RWF from ...` — incoming personal transfers
- `*113*R*A bank deposit of <amount> RWF ...` — bank deposits
- `*143*R*Y'ello, the transaction with amount <amount> RWF ...`
- `... DEPOSIT RWF <amount> ...` — statement-style deposit lines

### Counted as SENT
- `Your payment of <amount> RWF to ...` — payments to people / merchants / bundles
- `*165*S*<amount> RWF transferred to ...` — outgoing transfers
- `You have transferred <amount> RWF to ...`
- `*164*S*Y'ello, A transaction of <amount> RWF by ...` — merchant debits
- `Yello! Umaze kugura ... igura <amount> RWF` — airtime/data bundle purchases
- `... withdrawn <amount> RWF from your mobile money account` — agent cash-out

### Skipped (not a money movement)
- One-time password (OTP) messages
- Reversal notices (`reversal has been initiated`, `has been reversed`) — these
  cancel a prior transaction, so counting them would double-count

The skipped count is shown in the report for transparency.

---

## How it works (briefly)

`transaction_processor.py` uses Python's `xml.etree.ElementTree.iterparse`
to stream through the XML element-by-element. This keeps memory usage low
even for backups with thousands of messages — no need to load the whole
document at once. Each element is freed (`elem.clear()`) after it's
processed.

All classification rules live in a single `RULES` list of `(label, regex)`
pairs. The first matching rule wins, and "skip" rules sit at the top so
OTPs and reversals never fall through into the money patterns.

---

## Limitations

- **Regex-based classification** — if MTN changes their SMS wording, the
  patterns may need to be updated. Unknown messages are not silently
  miscategorized; they go into the "skipped" bucket and are reported.
- **Currency** — assumes all amounts are in **RWF** (Rwandan Francs).
- **No fee accounting** — the report counts the transaction amount itself,
  not transaction fees deducted by MTN.
- **Reversals are skipped, not netted** — if a sent transaction was later
  reversed, the original is still counted as sent. Both the original send
  and the reversal notice would be needed to net them out; the current
  approach is to count the send and skip the reversal SMS.

---

## Example: tested results

Run against the provided `modified_sms_v2.xml` (1,691 SMS entries):

| Category | Count | Total (RWF) |
| --- | ---:| ---:|
| Sent | 1,366 | 16,531,043 |
| Received | 315 | 16,435,353 |
| Skipped (OTPs, reversals) | 10 | — |
| **Grand total transactions** | **1,681** | **32,966,396** |
