import csv
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

class SecurityAuditApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Security Audit Tool")
        self.root.geometry("900x700")
        
        # Load data
        self.chapters = self.load_csv("chapters.csv")
        self.audit_info = self.load_csv("audit_info.csv")
        self.remediations = self.load_csv("remediation.csv")
        
        # Create mappings
        self.audit_map = {row["chapter_id"]: row for row in self.audit_info}
        self.rem_map = {row["chapter_id"]: row for row in self.remediations}
        self.chapter_map = {row["chapter_id"]: row for row in self.chapters}
        
        # Response options
        self.option_labels = {
            "1": "Nu știu",
            "2": "Implementat",
            "3": "Neimplementat",
            "4": "Implementat parțial"
        }
        
        # Store responses
        self.responses = {}
        self.current_index = 0
        
        # Create GUI elements
        self.create_widgets()
        
        # Start with first question
        self.show_question()
    
    def load_csv(self, filename):
        try:
            with open(filename, newline='', encoding="utf-8") as f:
                return list(csv.DictReader(f, delimiter=','))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {filename}: {str(e)}")
            return []
    
    def create_widgets(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Question display
        self.question_label = ttk.Label(
            self.main_frame, 
            text="", 
            wraplength=800,
            font=('Arial', 12, 'bold')
        )
        self.question_label.pack(pady=(10, 20))
        
        # Response buttons
        self.response_frame = ttk.Frame(self.main_frame)
        self.response_frame.pack(pady=10)
        
        self.response_var = tk.StringVar()
        
        self.radio1 = ttk.Radiobutton(
            self.response_frame, 
            text="Nu știu", 
            variable=self.response_var, 
            value="1"
        )
        self.radio1.grid(row=0, column=0, padx=5, sticky="w")
        
        self.radio2 = ttk.Radiobutton(
            self.response_frame, 
            text="Implementat", 
            variable=self.response_var, 
            value="2"
        )
        self.radio2.grid(row=1, column=0, padx=5, sticky="w")
        
        self.radio3 = ttk.Radiobutton(
            self.response_frame, 
            text="Neimplementat", 
            variable=self.response_var, 
            value="3"
        )
        self.radio3.grid(row=2, column=0, padx=5, sticky="w")
        
        self.radio4 = ttk.Radiobutton(
            self.response_frame, 
            text="Implementat parțial", 
            variable=self.response_var, 
            value="4"
        )
        self.radio4.grid(row=3, column=0, padx=5, sticky="w")
        
        # Navigation buttons
        self.nav_frame = ttk.Frame(self.main_frame)
        self.nav_frame.pack(pady=20)
        
        self.prev_btn = ttk.Button(
            self.nav_frame, 
            text="← Întrebarea anterioară", 
            command=self.prev_question
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = ttk.Button(
            self.nav_frame, 
            text="Întrebarea următoare →", 
            command=self.next_question
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        self.finish_btn = ttk.Button(
            self.nav_frame, 
            text="Finalizează auditul", 
            command=self.finish_audit
        )
        self.finish_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress label
        self.progress_label = ttk.Label(self.main_frame, text="")
        self.progress_label.pack(pady=10)
        
        # Chapter hierarchy tree
        self.tree_frame = ttk.Frame(self.main_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.tree = ttk.Treeview(self.tree_frame, columns=('response'), show='tree headings')
        self.tree.heading('#0', text='Secțiune')
        self.tree.heading('response', text='Răspuns')
        self.tree.column('response', width=150, anchor='center')
        
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        # Populate tree
        self.build_chapter_tree()
        
        # Bind tree selection
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
    
    def build_chapter_tree(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Build hierarchy
        nodes = {}
        
        # First pass - create all nodes
        for chapter in self.chapters:
            cid = chapter['chapter_id']
            hindex = chapter['hierarchy_index']
            title = chapter['title']
            
            parts = hindex.split('.')
            parent = ''
            
            # Build parent path
            for i in range(len(parts)-1):
                parent_part = '.'.join(parts[:i+1])
                if parent_part not in nodes:
                    # Find the chapter with this hierarchy index
                    for c in self.chapters:
                        if c['hierarchy_index'] == parent_part:
                            nodes[parent_part] = self.tree.insert(
                                nodes.get('.'.join(parts[:i]), ''),
                                'end',
                                text=f"{parent_part} {c['title']}",
                                values=(self.responses.get(c['chapter_id'], ''))
                            )
                            break
            
            # Add current node if not already added
            if hindex not in nodes:
                nodes[hindex] = self.tree.insert(
                    nodes.get('.'.join(parts[:-1]), ''),
                    'end',
                    text=f"{hindex} {title}",
                    values=(self.responses.get(cid, ''))
                )
        
        # Update all responses in the tree
        for cid, resp in self.responses.items():
            chapter = self.chapter_map[cid]
            hindex = chapter['hierarchy_index']
            if hindex in nodes:
                self.tree.item(nodes[hindex], values=(self.option_labels.get(resp, '')))
    
    def show_question(self):
        if self.current_index < 0 or self.current_index >= len(self.chapters):
            return
            
        chapter = self.chapters[self.current_index]
        self.question_label.config(text=f"{chapter['hierarchy_index']}. {chapter['title']}")
        
        # Set current response if exists
        if chapter['chapter_id'] in self.responses:
            self.response_var.set(self.responses[chapter['chapter_id']])
        else:
            self.response_var.set("1")  # Default to "Nu știu"
        
        # Update progress
        self.progress_label.config(
            text=f"Întrebarea {self.current_index + 1} din {len(self.chapters)}"
        )
        
        # Update navigation buttons state
        self.prev_btn.state(['!disabled' if self.current_index > 0 else 'disabled'])
        self.next_btn.state(['!disabled' if self.current_index < len(self.chapters) - 1 else 'disabled'])
    
    def save_response(self):
        if self.current_index < 0 or self.current_index >= len(self.chapters):
            return
            
        chapter = self.chapters[self.current_index]
        cid = chapter['chapter_id']
        hindex = chapter['hierarchy_index']
        resp = self.response_var.get()
        
        self.responses[cid] = resp
        
        # Propagate response to children if not "Implementat parțial"
        if resp in ["1", "2", "3"]:
            self.propagate_response(hindex, resp)
        
        # Update tree
        self.build_chapter_tree()
    
    def propagate_response(self, current_index, response_value):
        for chapter in self.chapters:
            cid = chapter["chapter_id"]
            hindex = chapter["hierarchy_index"]
            if hindex != current_index and hindex.startswith(current_index + ".") and cid not in self.responses:
                self.responses[cid] = response_value
    
    def next_question(self):
        self.save_response()
        self.current_index += 1
        self.show_question()
    
    def prev_question(self):
        self.save_response()
        self.current_index -= 1
        self.show_question()
    
    def on_tree_select(self, event):
        selected_item = self.tree.focus()
        item_text = self.tree.item(selected_item, 'text')
        
        # Find the chapter that matches this item
        for idx, chapter in enumerate(self.chapters):
            if f"{chapter['hierarchy_index']} {chapter['title']}" == item_text:
                self.current_index = idx
                self.show_question()
                break
    
    def finish_audit(self):
        self.save_response()
        
        # Check if all questions answered
        unanswered = [c['title'] for c in self.chapters if c['chapter_id'] not in self.responses]
        
        if unanswered:
            if not messagebox.askyesno(
                "Confirmare",
                f"{len(unanswered)} întrebări nu au răspuns. Doriți să continuați oricum?"
            ):
                return
        
        # Generate PDF with recommendations
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        pdf_added = False
        
        for cid, resp in self.responses.items():
            if resp in ["1", "3"]:  # only for "Nu știu" or "Neimplementat"
                chapter = self.chapter_map[cid]
                audit = self.audit_map.get(cid, {}).get("method", "Nedefinit")
                remediation = self.rem_map.get(cid, {}).get("remediation", "Nedefinit")
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
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile="recomandari_securitate.pdf"
            )
            
            if file_path:
                pdf.output(file_path)
                messagebox.showinfo(
                    "Audit completat",
                    f"Raportul a fost generat: {file_path}"
                )
        else:
            messagebox.showinfo(
                "Audit completat",
                "Sistem securizat: toate măsurile sunt implementate."
            )
        
        # Show summary
        self.show_summary()
    
    def show_summary(self):
        summary_win = tk.Toplevel(self.root)
        summary_win.title("Rezumat audit")
        summary_win.geometry("800x600")
        
        # Count responses
        counts = {
            "Implementat": 0,
            "Neimplementat": 0,
            "Implementat parțial": 0,
            "Nu știu": 0
        }
        
        for resp in self.responses.values():
            counts[self.option_labels.get(resp, "Nu știu")] += 1
        
        # Summary frame
        summary_frame = ttk.Frame(summary_win, padding="10")
        summary_frame.pack(fill=tk.BOTH, expand=True)
        
        # Summary stats
        stats_frame = ttk.Frame(summary_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(stats_frame, text="Statistici:", font=('Arial', 12, 'bold')).pack(anchor='w')
        
        for label, count in counts.items():
            ttk.Label(
                stats_frame, 
                text=f"{label}: {count} ({count/len(self.responses)*100:.1f}%)"
            ).pack(anchor='w', padx=20)
        
        # Details
        details_frame = ttk.Frame(summary_frame)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(details_frame, text="Detalii recomandări:", font=('Arial', 12, 'bold')).pack(anchor='w')
        
        text_area = ScrolledText(details_frame, wrap=tk.WORD, width=80, height=20)
        text_area.pack(fill=tk.BOTH, expand=True)
        
        for cid, resp in self.responses.items():
            if resp in ["1", "3"]:  # "Nu știu" or "Neimplementat"
                chapter = self.chapter_map[cid]
                remediation = self.rem_map.get(cid, {}).get("remediation", "Nedefinit")
                
                text_area.insert(tk.END, f"\n🔹 {chapter['title']}\n")
                text_area.insert(tk.END, f"Remediere: {remediation}\n")
                text_area.insert(tk.END, "-"*80 + "\n")
        
        text_area.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = SecurityAuditApp(root)
    root.mainloop()