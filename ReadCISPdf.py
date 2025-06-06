import fitz  # PyMuPDF
import csv
import re

# Deschidere PDF
doc = fitz.open("CIS_Ubuntu_Linux_14.04_LTS_Benchmark_v2.1.0_ARCHIVE.pdf")

# 1. Extrage capitolele din cuprins
chapters = []
chapter_map = {}  # title -> (chapter_id, page_number)
chapter_id = 0
toc_found = False
toc_started = False

for page_number, page in enumerate(doc, start=1):
    text = page.get_text()

    # Începem extragerea după ce detectăm "Table of Contents"
    if not toc_started and "Table of Contents" in text:
        toc_started = True

    if toc_started:
        lines = text.split("\n")
        for line in lines:
            match = re.match(r"^(\d+(\.\d+)+)\s+(.+?)\s+\.{3,}\s+(\d+)$", line.strip())
            if match:
                number, _, title, pg = match.groups()
                full_title = f"{number} {title}"
                pg_num = int(pg)
                if full_title not in chapter_map:
                    chapter_id += 1
                    chapters.append((chapter_id, full_title, pg_num))
                    chapter_map[full_title] = (chapter_id, pg_num)

        if "Appendix" in text:
            break  # sfârșitul cuprinsului


# 2. Parcurge restul paginilor pentru a extrage audit/remediation
audit_info = []
remediations = []

current_chapter_id = None
current_chapter_title = None

chapter_titles = list(chapter_map.keys())
chapter_titles.sort(key=lambda x: -len(x))  # cele mai lungi potriviri mai întâi

for page_number, page in enumerate(doc, start=1):
    text = page.get_text()
    lines = text.split("\n")
    joined_text = "\n".join(lines)

    # Găsește capitolul curent pe bază de titlu
    for title in chapter_titles:
        if title in joined_text:
            current_chapter_title = title
            current_chapter_id, _ = chapter_map[title]
            break

    # Caută toate blocurile de tip Audit: ... Output: ... Remediation:
    audits = re.findall(r"Audit:(.*?)(Remediation:|$)", joined_text, re.DOTALL)
    for audit_text, _ in audits:
        audit_text = audit_text.strip()
        # caută eventual output:
        output_match = re.search(r"Output:(.*)", audit_text, re.DOTALL)
        if output_match:
            method = audit_text.split("Output:")[0].strip()
            output = output_match.group(1).strip()
        else:
            method = audit_text
            output = ""
        if current_chapter_id:
            audit_info.append((current_chapter_id, method, output, page_number))

    # Remediation
    remediation_matches = re.findall(r"Remediation:(.*?)(\n[A-Z][a-z]+:|\Z)", joined_text, re.DOTALL)
    for remediation_text, _ in remediation_matches:
        remediation = remediation_text.strip()
        if remediation and current_chapter_id:
            remediations.append((current_chapter_id, remediation, page_number))

# 3. Scriere CSV
with open("chapters.csv", "w", newline='', encoding="utf-8") as f:
    csv.writer(f).writerows([["chapter_id", "title", "page_number"]] + chapters)

with open("audit_info.csv", "w", newline='', encoding="utf-8") as f:
    csv.writer(f).writerows([["chapter_id", "method", "output", "page_number"]] + audit_info)

with open("remediation.csv", "w", newline='', encoding="utf-8") as f:
    csv.writer(f).writerows([["chapter_id", "remediation", "page_number"]] + remediations)

print("CSV-urile au fost completate corect.")
