
import re
import xml.etree.ElementTree as ET
import os
xml_path = os.path.join(os.path.dirname(__file__), "modified_sms_v2.xml")
tree = ET.parse(xml_path)
root = tree.getroot()
messages = root.findall("sms")

RECEIVED_RE = re.compile(r"You have received\s+([\d,]+)\s*RWF")
SENT_RE     = re.compile(r"You have transferred\s+([\d,]+)\s*RWF")


received_amounts = []
sent_amounts = []

for sms in messages:
    body = sms.get("body", "")

    received_match = RECEIVED_RE.search(body)
    if received_match:
        amount = int(received_match.group(1).replace(",", ""))
        received_amounts.append(amount)
        continue

    sent_match = SENT_RE.search(body)
    if sent_match:
        amount = int(sent_match.group(1).replace(",", ""))
        sent_amounts.append(amount)

print("\n===== RECEIVED =====")
for amount in received_amounts:
    print(f"  You have received {amount:,} RWF")

print("\n===== SENT (transferred) =====")
for amount in sent_amounts:
    print(f"  You have transferred {amount:,} RWF")

received_total = 0
for amount in received_amounts:
    received_total += amount

sent_total = 0
for amount in sent_amounts:
    sent_total += amount

grand_total = received_total + sent_total

print("\n           TOTALS ")
print()
print(f"  Total RECEIVED : {received_total:,} RWF")
print(f"  Total SENT     : {sent_total:,} RWF")
print(f"  GRAND TOTAL    : {grand_total:,} RWF")
