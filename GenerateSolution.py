import csv
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Încarcă datele CSV
def load_csv(filename):
    with open(filename, newline='', encoding="utf-8") as f:
        return list(csv.DictReader(f))

chapters = load_csv("chapters.csv")
audit_info = load_csv("audit_info.csv")
remediations = load_csv("remediation.csv")

# Mapări pentru acces rapid
audit_map = {row["chapter_id"]: row for row in audit_info}
rem_map = {row["chapter_id"]: row for row in remediations}
chapter_map = {row["chapter_id"]: row for row in chapters}

# Posibile răspunsuri
option_labels = {
    "1": "Nu știu",
    "2": "Implementat",
    "3": "Neimplementat",
    "4": "Implementat parțial"
}

# Pregătește PDF
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font("Arial", size=12)
pdf_added = False

# Dictionar de răspunsuri (chapter_id -> răspuns)
responses = {}

# Funcție pentru propagare
def propagate_response(current_index, response_value):
    for chapter in chapters:
        cid = chapter["chapter_id"]
        hindex = chapter["hierarchy_index"]
        if hindex != current_index and hindex.startswith(current_index + ".") and cid not in responses:
            responses[cid] = response_value

# Chestionar
for chapter in chapters:
    cid = chapter["chapter_id"]
    hindex = chapter["hierarchy_index"]
    title = chapter["title"]

    if cid in responses:
        continue  # deja răspuns moștenit

    print(f"\n🔒 Întrebare: {title}")
    print("1) Nu știu")
    print("2) Implementat")
    print("3) Neimplementat")
    print("4) Implementat parțial")
    resp = input("Răspuns (1/2/3/4): ").strip()

    if resp not in option_labels:
        print("Răspuns invalid. Se consideră 'Nu știu'")
        resp = "1"

    responses[cid] = resp

    if resp in ["1", "2", "3"]:
        propagate_response(hindex, resp)

# Generare PDF dacă este nevoie
for cid, resp in responses.items():
    if resp in ["1", "3"]:  # doar dacă nu e implementat sau necunoscut
        chapter = chapter_map[cid]
        audit = audit_map.get(cid, {}).get("method", "Nedefinit")
        remediation = rem_map.get(cid, {}).get("remediation", "Nedefinit")
        title = chapter["title"]

        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"{title}", ln=True)

        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, f"Audit:\n{audit}")
        pdf.ln(1)
        pdf.multi_cell(0, 10, f"Remediere:\n{remediation}")
        pdf_added = True

if pdf_added:
    pdf.output("recomandari_securitate.pdf")
    print("\n PDF generat: recomandari_securitate.pdf")
else:
    print("\n Sistem securizat: toate măsurile sunt implementate.")
