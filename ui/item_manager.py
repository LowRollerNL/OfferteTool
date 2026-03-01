import customtkinter as ctk
from tkinter import StringVar, BooleanVar
from models import get_items, create_item, update_item, delete_item

class ItemManager:
    """Artikelenlijst + toevoegen + inline bewerken in één scherm"""

    def __init__(self, parent):
        self.parent = parent
        self.window = ctk.CTkFrame(parent)
        self.window.pack(fill="both", expand=True, padx=10, pady=10)

        # Formulier om nieuw artikel toe te voegen
        form_frame = ctk.CTkFrame(self.window)
        form_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Naam:").grid(row=0, column=0, padx=5, pady=5)
        self.name_var = StringVar()
        ctk.CTkEntry(form_frame, textvariable=self.name_var).grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="Prijs:").grid(row=1, column=0, padx=5, pady=5)
        self.price_var = StringVar()
        ctk.CTkEntry(form_frame, textvariable=self.price_var).grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(form_frame, text="BTW %:").grid(row=2, column=0, padx=5, pady=5)
        self.btw_var = StringVar(value="21")
        ctk.CTkEntry(form_frame, textvariable=self.btw_var).grid(row=2, column=1, padx=5, pady=5)

        self.in_btw_var = BooleanVar(value=False)
        ctk.CTkCheckBox(form_frame, text="In de BTW?", variable=self.in_btw_var).grid(row=3, column=0, columnspan=2, pady=5)

        ctk.CTkButton(form_frame, text="Voeg toe", command=self.add_item).grid(row=4, column=0, columnspan=2, pady=10)

        # Artikelenlijst frame
        self.list_frame = ctk.CTkFrame(self.window)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.load_items()

    def load_items(self):
        """Laad en toon alle artikelen met inline bewerkvelden"""
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        items = get_items()
        for item in items:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", pady=2, padx=5)

            # Variabelen per item voor inline bewerken
            name_var = StringVar(value=item[1])
            price_var = StringVar(value=f"{item[2]:.2f}")
            btw_var = StringVar(value=str(item[3]))
            in_btw_var = BooleanVar(value=(item[3] != 0))

            # Inline velden
            ctk.CTkEntry(row, textvariable=name_var, width=325).pack(side="left", padx=5)
            ctk.CTkEntry(row, textvariable=price_var, width=80).pack(side="left", padx=5)
            ctk.CTkEntry(row, textvariable=btw_var, width=50).pack(side="left", padx=5)
            ctk.CTkCheckBox(row, text="In BTW?", variable=in_btw_var).pack(side="left", padx=5)

            # Opslaan knop
            def make_save(item_id, n_var=name_var, p_var=price_var, b_var=btw_var, btw_chk=in_btw_var):
                def save():
                    try:
                        price = float(p_var.get())
                        btw_value = float(b_var.get()) if btw_chk.get() else 0
                        if btw_chk.get():
                            price = round(price / (1 + btw_value / 100), 2)
                        update_item(item_id, n_var.get().strip(), price, btw_value)
                        self.load_items()
                    except ValueError:
                        print("Prijs en BTW moeten getallen zijn")
                return save

            ctk.CTkButton(row, text="Bewerk", width=70, command=lambda i=item: self.edit_item_popup(i)  # popup openen
            ).pack(side="right", padx=5)

            # Verwijderen knop
            ctk.CTkButton(row, text="Verwijder", width=70, fg_color="red", command=lambda i=item[0]: self.remove_item(i)).pack(side="right", padx=5)

    def add_item(self):
        """Voeg nieuw artikel toe aan database"""
        try:
            name = self.name_var.get().strip()
            price = float(self.price_var.get())
            btw = float(self.btw_var.get()) if self.in_btw_var.get() else 0
            if self.in_btw_var.get():
                price = round(price / (1 + btw / 100), 2)
        except ValueError:
            print("Prijs en BTW moeten getallen zijn")
            return

        if not name:
            print("Naam is verplicht")
            return

        create_item(name, price, btw)
        self.name_var.set("")
        self.price_var.set("")
        self.btw_var.set("21")
        self.in_btw_var.set(False)
        self.load_items()

    def remove_item(self, item_id):
        """Verwijder artikel"""
        delete_item(item_id)
        self.load_items()
        
        
    def edit_item_popup(self, item):
        """Popup om een bestaand artikel te bewerken"""
        root = self.window.winfo_toplevel()  # haal het bovenliggende Tk-venster van het frame
        edit_window = ctk.CTkToplevel(root)
        edit_window.title("Artikel bewerken")
        edit_window.geometry("400x250")
        edit_window.grab_set()

        # Variabelen met huidige waarden
        name_var = StringVar(value=item[1])
        price_var = StringVar(value=str(item[2]))
        btw_var = StringVar(value=str(item[3]))
        in_btw_var = ctk.BooleanVar(value=(item[3] != 0))  # True als BTW niet 0

        # Formulier frame
        form_frame = ctk.CTkFrame(edit_window)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Naam
        ctk.CTkLabel(form_frame, text="Naam:").grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkEntry(form_frame, textvariable=name_var, width=300, height=30).grid(row=0, column=1, padx=5, pady=5)

        # Prijs
        ctk.CTkLabel(form_frame, text="Prijs:").grid(row=1, column=0, padx=5, pady=5)
        ctk.CTkEntry(form_frame, textvariable=price_var, width=150, height=30).grid(row=1, column=1, padx=5, pady=5)

        # BTW %
        ctk.CTkLabel(form_frame, text="BTW %:").grid(row=2, column=0, padx=5, pady=5)
        ctk.CTkEntry(form_frame, textvariable=btw_var, width=150, height=30).grid(row=2, column=1, padx=5, pady=5)

        # Checkbox “In de BTW?”
        ctk.CTkCheckBox(form_frame, text="In de BTW?", variable=in_btw_var).grid(row=3, column=0, columnspan=2, pady=5)

        # Opslaan knop
        def save_changes():
            try:
                price = float(price_var.get())
                btw_value = float(btw_var.get()) if in_btw_var.get() else 0

                # Als checkbox aan: prijs is inclusief BTW → omzet exclusief berekenen
                if in_btw_var.get():
                    price = round(price / (1 + btw_value / 100), 2)

                # Update in database
                update_item(
                    item[0],
                    name_var.get().strip(),
                    price,
                    btw_value
                )
                edit_window.destroy()
                self.load_items()  # refresh lijst
            except ValueError:
                print("Prijs en BTW moeten getallen zijn")

        ctk.CTkButton(form_frame, text="Opslaan", command=save_changes).grid(row=4, column=0, columnspan=2, pady=10)    