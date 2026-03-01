import customtkinter as ctk
from tkinter import messagebox
from rapidfuzz import process, fuzz
import re
from models import create_customer, update_customer


def open_customer_popup(parent, refresh_callback, customer=None):
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

    def is_valid_email(email):
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    common_domains = ["gmail.com", "hotmail.com", "outlook.com", "icloud.com", "yahoo.com", "ziggo.nl", "kpn.nl"]

    def save_customer():
        name = name_var.get().strip()
        email = email_var.get().strip()

        if not name or not email:
            messagebox.showerror("Fout", "Naam en e-mail zijn verplicht!")
            return

        if not is_valid_email(email):
            messagebox.showerror("Fout", "Ongeldig e-mailadres!")
            return

        local_part, domain_part = email.split("@")
        best_match = process.extractOne(domain_part, common_domains, scorer=fuzz.ratio)

        if best_match and best_match[1] > 80 and best_match[0] != domain_part:
            if messagebox.askyesno(
                "Domein suggestie",
                f"Bedoelde u {local_part}@{best_match[0]}?"
            ):
                email = f"{local_part}@{best_match[0]}"

        if customer_id:
            update_customer(
                customer_id,
                name=name,
                email=email,
                phone=phone_var.get().strip(),
                address=street_var.get().strip(),
                postal=postcode_var.get().strip(),
                city=city_var.get().strip()
            )
        else:
            create_customer(
                name=name,
                email=email,
                phone=phone_var.get().strip(),
                address=street_var.get().strip(),
                postal=postcode_var.get().strip(),
                city=city_var.get().strip()
            )

        refresh_callback()
        popup.destroy()

    # UI
    fields = [
        ("Naam (verplicht):", name_var),
        ("E-mail (verplicht):", email_var),
        ("Telefoon:", phone_var),
        ("Adres + huisnr:", street_var),
        ("Postcode:", postcode_var),
        ("Plaats:", city_var),
    ]

    for label, var in fields:
        ctk.CTkLabel(popup, text=label).pack(pady=5, anchor="w", padx=20)
        ctk.CTkEntry(popup, textvariable=var).pack(pady=5, fill="x", padx=20)

    ctk.CTkButton(popup, text="Opslaan", command=save_customer).pack(pady=20)