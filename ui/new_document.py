import customtkinter as ctk
from datetime import datetime
from models import (
    create_document, add_document_line, get_customers,
    create_customer, get_documents, update_document,
    delete_document_lines, get_document_lines, get_open_customers, generate_document_number, get_items, get_settings
)
from ui.customer_popup import open_customer_popup
from ui.dashboard import DashboardView
from calculations import calculate_line_total, calculate_btw
from tkinter import Toplevel, StringVar, Label, Entry, Button


class NewDocumentView(ctk.CTkFrame):
    def __init__(self, parent, doc_type, document_id=None):
        super().__init__(parent)

        self.doc_type = doc_type
        self.document_id = document_id
        self.lines = []

        self.customer_var = ctk.StringVar()
        self.pack(fill="both", expand=True)

        # UI bouwen
        self.build_ui()

        # Bestaand document laden indien nodig
        if self.document_id:
            self.load_existing_document()

    # ==========================
    # UI opbouwen
    # ==========================
    def build_ui(self):
        # Titel
        title = "Nieuwe Offerte" if self.doc_type == "offerte" else "Nieuwe Factuur"
        ctk.CTkLabel(self, text=title, font=("Arial", 28, "bold")).pack(pady=20)

        # Klant selectie
        self.customer_var = ctk.StringVar(value="Kies bestaande klant")
        frame_top = ctk.CTkFrame(self)
        frame_top.pack(pady=10, fill="x", padx=20)
        
        self.customer_dropdown = ctk.CTkOptionMenu(frame_top, values=[], variable=self.customer_var)
        self.customer_dropdown.pack(side="left", padx=5)
        
        ctk.CTkButton(frame_top, text="Nieuwe klant",
                      command=lambda: open_customer_popup(self, self.refresh_customers)).pack(side="left", padx=10)
        
        self.refresh_customers()
        self.customer_var.trace("w", lambda *args: self.load_customer_info())

        self.customer_info_label = ctk.CTkLabel(self, text="", justify="left")
        self.customer_info_label.pack(pady=5)

        # -------------------------
        # Header met kolomnamen (grid)
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=20, pady=(0,5))
        
        headers = ["Omschrijving", "", "Aantal", "Prijs", "BTW %", "Totaal", ""]
        widths = [250, 30, 80, 100, 80, 100, 40]  # breedtes gelijk aan add_line()
        
        for col, (h, w) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(header_frame, text=h, width=w, anchor="center", font=("Arial", 12, "bold"))
            label.grid(row=0, column=col, padx=2)

        # -------------------------
        # Frame voor regels (lines)
        self.lines_frame = ctk.CTkFrame(self)
        self.lines_frame.pack(padx=20, pady=5, fill="x")

        # -------------------------
        # Knop om regel toe te voegen
        add_line_frame = ctk.CTkFrame(self)
        add_line_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkButton(add_line_frame, text="Regel toevoegen", command=self.add_line).pack(side="left")
        
        # -------------------------
        # Totaal label
        self.total_label = ctk.CTkLabel(self, text="Totaal: € 0.00", font=("Arial", 18))
        self.total_label.pack(pady=10)

        # -------------------------
        # Opslaan knop
        ctk.CTkButton(self, text="Opslaan", command=self.save_document).pack(pady=20)

    # ==========================
    # Klantenlijst ophalen
    # ==========================
    def refresh_customers(self):
        customers = get_customers()  # altijd alle klanten
        self.customers_map = {c["name"]: c["id"] for c in customers}

        # Voeg placeholder toe als eerste optie
        dropdown_values = ["Kies bestaande klant"] + list(self.customers_map.keys())
        self.customer_dropdown.configure(values=dropdown_values)

        # Zet de dropdown terug op de placeholder als er nog niets geselecteerd is
        if self.customer_var.get() not in self.customers_map:
            self.customer_var.set("Kies bestaande klant")

    def load_customer_info(self):
        name = self.customer_var.get()
        if name in self.customers_map:
            customer_id = self.customers_map[name]
            customer = [c for c in get_customers() if c["id"] == customer_id][0]
            info_text = f"Naam: {customer[1]}\nEmail: {customer[2] or ''}\nTelefoon: {customer[3] or ''}\nAdres: {customer[4] or ''}"
            self.customer_info_label.configure(text=info_text)
        else:
            self.customer_info_label.configure(text="")  

    # ==========================
    # Nieuwe regel toevoegen (met grid!)
    # ==========================
    def add_line(self, description_value="", quantity_value="1", price_value="", btw_value="21"):
        row_frame = ctk.CTkFrame(self.lines_frame)
        row_frame.pack(pady=2, fill="x")

        # ==========================
        # Variabelen
        # ==========================
        description_var = ctk.StringVar(value=description_value)
        quantity_var = ctk.StringVar(value=quantity_value)
        price_var = ctk.StringVar(value=price_value)
        btw_var = ctk.StringVar(value=btw_value)

        # Beschrijving max 50 tekens
        def truncate_description(*args):
            val = description_var.get()
            if len(val) > 50:
                description_var.set(val[:50])
        description_var.trace("w", truncate_description)

        # ==========================
        # Entry + Suggesties
        # ==========================
        description_entry = ctk.CTkEntry(row_frame, textvariable=description_var, width=250)
        suggestion_frame = ctk.CTkFrame(self.master, fg_color="grey", border_color="black", border_width=1)
        suggestion_frame.place(x=0, y=0)
        suggestion_frame.lower()
        suggestion_labels = []

        # Artikelenlijst
        self.items_list = get_items()
        item_names = [it[1] for it in self.items_list]

        def update_suggestions(event=None, force_show=False):
            typed = description_var.get().lower()
            for lbl in suggestion_labels:
                lbl.destroy()
            suggestion_labels.clear()

            matches = [name for name in item_names if typed in name.lower()] if not force_show else item_names
            if not matches:
                suggestion_frame.lower()
                return

            # positie onder entry
            x = description_entry.winfo_rootx() - self.master.winfo_rootx()
            y = description_entry.winfo_rooty() - self.master.winfo_rooty() + description_entry.winfo_height()
            suggestion_frame.place(x=x, y=y)
            suggestion_frame.lift()

            for match in matches[:20]:
                lbl = ctk.CTkLabel(suggestion_frame, text=match, fg_color="grey", text_color="white", cursor="hand2")
                lbl.pack(fill="x", pady=1)
                suggestion_labels.append(lbl)

                def select_match(m=match):
                    description_var.set(m)
                    item = next(it for it in self.items_list if it[1] == m)
                    price_var.set(str(item[2]))
                    btw_var.set(str(item[3]))
                    suggestion_frame.lower()

                lbl.bind("<Button-1>", lambda e, m=match: select_match(m))

        # Dropdown-button
        def toggle_dropdown():
            update_suggestions(force_show=True)
        dropdown_btn = ctk.CTkButton(row_frame, text="▼", width=30, command=toggle_dropdown)

        description_entry.bind("<KeyRelease>", update_suggestions)
        description_entry.bind("<FocusIn>", update_suggestions)

        # Hide suggestions veilig maken
        def hide_suggestions(event):
            if not suggestion_frame.winfo_exists():
                return
            if event.widget not in [description_entry, dropdown_btn]:
                suggestion_frame.lower()

        # Bind per lijn ipv master globale bind
        description_entry.bind("<FocusOut>", hide_suggestions)

        # ==========================
        # Andere velden
        # ==========================
        quantity_entry = ctk.CTkEntry(row_frame, textvariable=quantity_var, width=80)
        price_entry = ctk.CTkEntry(row_frame, textvariable=price_var, width=100)
        btw_entry = ctk.CTkEntry(row_frame, textvariable=btw_var, width=80)
        total_label = ctk.CTkLabel(row_frame, text="€ 0.00", width=100)

        # Update total
        def update_total(event=None):
            try:
                q = float(quantity_var.get() or 0)
                p = float(price_var.get() or 0)
                b = float(btw_var.get() or 0)
                total_excl = calculate_line_total(q, p)
                total_incl = total_excl + calculate_btw(total_excl, b)
                total_label.configure(text=f"€ {total_incl:.2f}")
            except:
                total_label.configure(text="€ 0.00")
            self.update_grand_total()

        quantity_entry.bind("<KeyRelease>", update_total)
        price_entry.bind("<KeyRelease>", update_total)
        btw_entry.bind("<KeyRelease>", update_total)

        # ==========================
        # Delete knop
        # ==========================
        def delete_this_line():
            row_frame.destroy()
            self.lines.remove(line_tuple)
            self.update_grand_total()
        delete_btn = ctk.CTkButton(row_frame, text="🗑", width=40, fg_color="red", hover_color="#cc0000", command=delete_this_line)

        # ==========================
        # Grid voor nette uitlijning
        # ==========================
        description_entry.grid(row=0, column=0, padx=2)
        dropdown_btn.grid(row=0, column=1, padx=2)
        quantity_entry.grid(row=0, column=2, padx=2)
        price_entry.grid(row=0, column=3, padx=2)
        btw_entry.grid(row=0, column=4, padx=2)
        total_label.grid(row=0, column=5, padx=2)
        delete_btn.grid(row=0, column=6, padx=2)

        # ==========================
        # Opslaan in lijst
        # ==========================
        line_tuple = (description_entry, quantity_entry, price_entry, btw_entry, total_label)
        self.lines.append(line_tuple)

        update_total()
        
    # ==========================
    # Destroy overschrijven om bindings op te ruimen
    # ==========================
    def destroy(self):
        # verwijder alle suggestion_frames
        for line in getattr(self, "lines", []):
            if len(line) == 6 and line[5].winfo_exists():
                line[5].destroy()
        super().destroy()        
        
    # ==========================
    # Update totaal
    # ==========================
    def update_grand_total(self):
        total = 0
        for line in self.lines:
            try:
                q = float(line[1].get() or 0)
                p = float(line[2].get() or 0)
                b = float(line[3].get() or 0)
                line_total = calculate_line_total(q, p) + calculate_btw(calculate_line_total(q, p), b)
                total += line_total
            except:
                continue
        self.total_label.configure(text=f"Totaal: € {total:.2f}")
    # ==========================
    # Document opslaan
    # ==========================
    def save_document(self):
        from datetime import datetime, timedelta
        from tkinter import messagebox

        # -------------------------
        # Validatie klant
        # -------------------------
        customer_name = self.customer_var.get().strip()

        if not customer_name or customer_name not in self.customers_map:
            messagebox.showerror("Fout", "Selecteer eerst een geldige klant.")
            return

        customer_id = self.customers_map[customer_name]

        # -------------------------
        # Bereken totals
        # -------------------------
        total_excl = 0
        total_btw = 0

        for line in self.lines:
            try:
                q = float(line[1].get() or 0)
                p = float(line[2].get() or 0)
                b = float(line[3].get() or 0)

                line_excl = calculate_line_total(q, p)
                line_btw = calculate_btw(line_excl, b)

                total_excl += line_excl
                total_btw += line_btw
            except ValueError:
                continue

        total_incl = total_excl + total_btw

        # -------------------------
        # Betalingstermijn & due_date
        # -------------------------
        settings = get_settings()
        term_days = int(settings.get("payment_term_days", 14))
        due_date = (datetime.now() + timedelta(days=term_days)).strftime("%Y-%m-%d")

        # -------------------------
        # Document opslaan
        # -------------------------
        if self.document_id:
            # UPDATE bestaand document
            doc_id = self.document_id

            update_document(doc_id, {
                "customer_id": customer_id,
                "total_excl": total_excl,
                "total_btw": total_btw,
                "total_incl": total_incl,
                "due_date": due_date
            })

            delete_document_lines(doc_id)

        else:
            # NIEUW document
            doc_data = {
                "type": self.doc_type,
                "number": generate_document_number(self.doc_type),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "due_date": due_date,
                "customer_id": customer_id,
                "status": "open",
                "total_excl": total_excl,
                "total_btw": total_btw,
                "total_incl": total_incl,
                "is_invoiced": 0
            }

            doc_id = create_document(doc_data)

        # -------------------------
        # Regels toevoegen
        # -------------------------
        for line in self.lines:
            try:
                description = line[0].get().strip()
                if not description:
                    continue

                q = float(line[1].get() or 0)
                p = float(line[2].get() or 0)
                b = float(line[3].get() or 0)

                line_excl = calculate_line_total(q, p)
                line_btw = calculate_btw(line_excl, b)
                total_line = line_excl + line_btw

                add_document_line(doc_id, {
                    "description": description,
                    "quantity": q,
                    "purchase_price": 0,
                    "sale_price": p,
                    "profit_percent": 0,
                    "btw_percent": b,
                    "total": total_line
                })

            except ValueError:
                continue

        # -------------------------
        # Terug naar overzicht
        # -------------------------
        self.destroy()
        from ui.overview import OverviewView
        OverviewView(self.master, self.doc_type)

    # ==========================
    # Laden bestaand document
    # ==========================
    def load_existing_document(self):
        doc = [d for d in get_documents(self.doc_type) if d["id"] == self.document_id][0]
        customer_id = doc["customer_id"]
        customer_name = [name for name, cid in self.customers_map.items() if cid == customer_id][0]
        self.customer_var.set(customer_name)
        self.load_customer_info()
        lines = get_document_lines(self.document_id)
        for line in lines:
            self.add_line(
                description_value=line[2],
                quantity_value=line[3],
                price_value=line[5],
                btw_value=line[7]
            )