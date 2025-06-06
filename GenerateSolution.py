import csv
from fpdf import FPDF

# Încarcă datele
def load_csv(filename):
    with open(filename, newline='', encoding="utf-8") as f:
        return list(csv.DictReader(f))

chapters = load_csv("chapters.csv")
audit_info = load_csv("audit_info.csv")
remediations = load_csv("remediation.csv")

# Dicționare pentru lookup rapid
audit_map = {row["chapter_id"]: row for row in audit_info}
rem_map = {row["chapter_id"]: row for row in remediations}

# Răspunsuri posibile
options = {
    "1": "Nu știu",
    "2": "Implementat",
    "3": "Neimplementat"
}

# Inițializare PDF
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font("Arial", size=12)
pdf_added = False

# Chestionar interactiv
for chapter in chapters:
    chapter_id = chapter["chapter_id"]
    title = chapter["title"]

    print(f"\n🔒 Întrebare: {title}")
    print("1) Nu știu")
    print("2) Implementat")
    print("3) Neimplementat")
    response = input("Răspuns (1/2/3): ").strip()

    if response not in options:
        print("Răspuns invalid. Se va considera ca 'Nu știu'")
        response = "1"

    if response in ["1", "3"]:  # Nu știu sau Neimplementat
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"{title}", ln=True)

        audit = audit_map.get(chapter_id, {}).get("method", "Fără date")
        remediation = rem_map.get(chapter_id, {}).get("remediation", "Fără instrucțiuni")

        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, f"Audit:\n{audit}")
        pdf.ln(1)
        pdf.multi_cell(0, 10, f"Remediere:\n{remediation}")
        pdf_added = True

# Finalizare
if pdf_added:
    pdf.output("recomandari_securitate.pdf")
    print("\n PDF generat: recomandari_securitate.pdf")
else:
    print("\n Sistem securizat: toate măsurile sunt implementate.")
