import customtkinter as ctk
from tkinter import Toplevel, Label, Entry, StringVar, Button, messagebox
from models import get_customers, create_customer, update_customer, delete_customer, get_connection, get_documents
from ui.customer_popup import open_customer_popup

class CustomerManagerView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Klantenbestand", font=("Arial", 24, "bold")).pack(pady=20)

        # --------------------------
        # Knop: Nieuwe klant
        # --------------------------
        ctk.CTkButton(
            self,
            text="Nieuwe klant",
            command=lambda: open_customer_popup(self, self.refresh_customers)
        ).pack(pady=10)

        # --------------------------
        # Frame met klantenlijst
        # --------------------------
        self.customers_frame = ctk.CTkFrame(self)
        self.customers_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.refresh_customers()

    def refresh_customers(self):
        # Alles leegmaken
        for widget in self.customers_frame.winfo_children():
            widget.destroy()

        customers = get_customers()

        # Header
        header = ctk.CTkFrame(self.customers_frame)
        header.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(header, text="Naam", width=300, anchor="w", font=("Arial", 14, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Telefoon", width=150, anchor="w", font=("Arial", 14, "bold")).pack(side="left", padx=5)

        # Klanten
        for customer in customers:
            row = ctk.CTkFrame(self.customers_frame)
            row.pack(fill="x", pady=2)

            # Klikbare naam
            name_btn = ctk.CTkButton(
                row,
                text=customer[1],
                width=300,
                anchor="w",
                fg_color="transparent",
                text_color="white",
                hover_color="#2a2a2a",
                command=lambda c=customer: self.show_customer_details(c)
            )
            name_btn.pack(side="left", padx=5)

            # Telefoon
            ctk.CTkLabel(
                row,
                text=customer[3] if len(customer) > 3 else "",
                width=150,
                anchor="w"
            ).pack(side="left", padx=5)

    # =======================
    # Nieuwe klant popup
    # =======================
    def open_customer_popup(parent, refresh_callback=None, customer=None):
        import customtkinter as ctk
        from tkinter import messagebox
        from rapidfuzz import process, fuzz
        import re
        from models import create_customer, update_customer

        popup = ctk.CTkToplevel(parent)
        popup.title("Klant bewerken" if customer else "Nieuwe klant")
        popup.geometry("400x520")
        popup.grab_set()

        customer_id = customer[0] if customer else None

        name_var = ctk.StringVar(value=customer[1] if customer else "")
        email_var = ctk.StringVar(value=customer[2] if customer else "")
        phone_var = ctk.StringVar(value=customer[3] if customer else "")
        street_var = ctk.StringVar(value=customer[4] if customer else "")
        postcode_var = ctk.StringVar(value=customer[5] if customer else "")
        city_var = ctk.StringVar(value=customer[6] if customer else "")

        # =============================
        # E-mail validatie
        # =============================
        common_domains = ["gmail.com", "hotmail.com", "outlook.com", "icloud.com", "yahoo.com", "ziggo.nl", "kpn.nl"]

        def is_valid_email(email):
            pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, email) is not None

        def save_customer():
            name = name_var.get().strip()
            email = email_var.get().strip()
            phone = phone_var.get().strip()
            address = street_var.get().strip()
            postal = postcode_var.get().strip()
            city = city_var.get().strip()

            if not name or not email:
                messagebox.showerror("Fout", "Naam en e-mail zijn verplicht!")
                return

            if not is_valid_email(email):
                messagebox.showerror("Fout", "Dit lijkt geen geldig e-mailadres!")
                return

            local_part, domain_part = email.split("@")
            best_match = process.extractOne(domain_part, common_domains, scorer=fuzz.ratio)

            if best_match and best_match[1] > 80 and best_match[0] != domain_part:
                if messagebox.askyesno("Domein suggestie", f"Bedoelde u {local_part}@{best_match[0]}?"):
                    email = f"{local_part}@{best_match[0]}"

            if customer_id:
                update_customer(
                    customer_id,
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    postal=postal,
                    city=city
                )
            else:
                create_customer(
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    postal=postal,
                    city=city
                )

            if refresh_callback:
                refresh_callback()

            popup.destroy()

        # UI velden
        for label, var in [
            ("Naam (verplicht):", name_var),
            ("E-mail (verplicht):", email_var),
            ("Telefoon:", phone_var),
            ("Adres + huisnr:", street_var),
            ("Postcode:", postcode_var),
            ("Plaats:", city_var)
        ]:
            ctk.CTkLabel(popup, text=label).pack(pady=5, anchor="w", padx=20)
            ctk.CTkEntry(popup, textvariable=var).pack(pady=5, fill="x", padx=20)

        ctk.CTkButton(popup, text="Opslaan", command=save_customer).pack(pady=15)

    # =======================
    # Klant bewerken
    # =======================
    def edit_customer(self, customer=None):
        """
        Als customer None is → nieuwe klant
        Anders → bestaande klant bewerken
        """
        popup = ctk.CTkToplevel(self)
        popup.title("Klant bewerken" if customer else "Nieuwe klant")
        popup.geometry("400x520")
        popup.grab_set()

        # Haal ID op (None bij nieuwe klant)
        customer_id = customer[0] if customer else None

        # Veilig bestaande waarden ophalen
        name_var = ctk.StringVar(value=customer[1] if customer and len(customer) > 1 else "")
        email_var = ctk.StringVar(value=customer[2] if customer and len(customer) > 2 else "")
        phone_var = ctk.StringVar(value=customer[3] if customer and len(customer) > 3 else "")
        street_var = ctk.StringVar(value=customer[4] if customer and len(customer) > 4 else "")
        postcode_var = ctk.StringVar(value=customer[5] if customer and len(customer) > 5 else "")
        city_var = ctk.StringVar(value=customer[6] if customer and len(customer) > 6 else "")

        # Labels en velden
        ctk.CTkLabel(popup, text="Naam (verplicht):").pack(pady=5, anchor="w", padx=20)
        ctk.CTkEntry(popup, textvariable=name_var).pack(pady=5, fill="x", padx=20)

        ctk.CTkLabel(popup, text="E-mail (verplicht):").pack(pady=5, anchor="w", padx=20)
        ctk.CTkEntry(popup, textvariable=email_var).pack(pady=5, fill="x", padx=20)

        ctk.CTkLabel(popup, text="Telefoon:").pack(pady=5, anchor="w", padx=20)
        ctk.CTkEntry(popup, textvariable=phone_var).pack(pady=5, fill="x", padx=20)

        ctk.CTkLabel(popup, text="Adres + huisnr:").pack(pady=5, anchor="w", padx=20)
        ctk.CTkEntry(popup, textvariable=street_var).pack(pady=5, fill="x", padx=20)

        ctk.CTkLabel(popup, text="Postcode:").pack(pady=5, anchor="w", padx=20)
        ctk.CTkEntry(popup, textvariable=postcode_var).pack(pady=5, fill="x", padx=20)

        ctk.CTkLabel(popup, text="Plaats:").pack(pady=5, anchor="w", padx=20)
        ctk.CTkEntry(popup, textvariable=city_var).pack(pady=5, fill="x", padx=20)

        # Functie opslaan
        def save_customer():
            name = name_var.get().strip()
            email = email_var.get().strip()
            phone = phone_var.get().strip()
            address = street_var.get().strip()
            postal = postcode_var.get().strip()
            city = city_var.get().strip()

            if not name or not email:
                messagebox.showerror("Fout", "Naam en e-mail zijn verplicht!")
                return

            # E-mail formaat check
            def is_valid_email(email):
                import re
                pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
                return re.match(pattern, email) is not None

            if not is_valid_email(email):
                messagebox.showerror("Fout", "Dit lijkt geen geldig e-mailadres!")
                return

            # Domein check
            common_domains = ["gmail.com", "hotmail.com", "outlook.com", "icloud.com", "yahoo.com", "ziggo.nl", "kpn.nl"]
            from rapidfuzz import process, fuzz
            try:
                local_part, domain_part = email.split("@")
            except ValueError:
                messagebox.showerror("Fout", "E-mailadres moet een '@' bevatten!")
                return

            best_match = process.extractOne(domain_part, common_domains, scorer=fuzz.ratio)
            if not best_match or best_match[1] < 80:
                messagebox.showerror("Fout", f"E-mailadres lijkt ongeldig: {email}\nGebruik een geldig domein zoals gmail.com, hotmail.com, etc.")
                return
            elif best_match[0] != domain_part:
                if messagebox.askyesno("Domein suggestie", f"Bedoelde u {local_part}@{best_match[0]}?"):
                    email = f"{local_part}@{best_match[0]}"

            # Opslaan
            if customer_id:  # bestaande klant
                update_customer(
                    customer_id,
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    postal=postal,
                    city=city
                )
            else:  # nieuwe klant
                create_customer(
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    postal=postal,
                    city=city
                )

            self.refresh_customers()
            popup.destroy()

        # Opslaan-knop
        ctk.CTkButton(popup, text="Opslaan", command=save_customer).pack(pady=15)

    # =======================
    # Klant verwijderen
    # =======================
    def delete_customer(self, customer_id):
        # Check of er nog openstaande facturen of offertes zijn
        documents = get_documents("factuur") + get_documents("offerte")
        has_open_docs = any(doc["customer_id"] == customer_id and doc["is_paid"] == 0 for doc in documents)  # doc[11] = is_paid

        if has_open_docs:
            from tkinter import messagebox
            messagebox.showerror(
                "Kan klant niet verwijderen",
                "Deze klant heeft nog openstaande facturen of offertes!"
            )
            return

        # Verwijder de klant uit DB
        delete_customer(customer_id)
                    
    def show_customer_details(self, customer):
        popup = ctk.CTkToplevel(self)
        popup.title("Klantgegevens")
        popup.geometry("400x450")
        popup.grab_set()

        # Gegevens veilig ophalen (ivm kolom volgorde)
        name = customer[1] if len(customer) > 1 else ""
        email = customer[2] if len(customer) > 2 else ""
        phone = customer[3] if len(customer) > 3 else ""
        address = customer[4] if len(customer) > 4 else ""
        postal = customer[5] if len(customer) > 5 else ""
        city = customer[6] if len(customer) > 6 else ""

        info_text = (
            f"Naam: {name}\n\n"
            f"E-mail: {email}\n"
            f"Telefoon: {phone}\n\n"
            f"Adres: {address}\n"
            f"Postcode: {postal}\n"
            f"Plaats: {city}"
        )

        ctk.CTkLabel(
            popup,
            text=info_text,
            justify="left"
        ).pack(padx=20, pady=20)

        button_frame = ctk.CTkFrame(popup)
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Bewerken",
            command=lambda: [popup.destroy(), self.edit_customer(customer)]
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Verwijderen",
            fg_color="red",
            hover_color="#cc0000",
            command=lambda: self._delete_and_refresh(customer[0], popup)
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            popup,
            text="Sluiten",
            command=popup.destroy
        ).pack(pady=10)
        
    def _delete_and_refresh(self, customer_id, popup):
        self.delete_customer(customer_id)  # verwijder uit DB
        popup.destroy()                     # sluit het popup
        self.refresh_customers()            # refresh de GUI lijst