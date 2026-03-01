import os
import customtkinter as ctk
from tkinter import StringVar, filedialog, Label, Text, END
from models import get_settings, save_settings
from PIL import Image, ImageTk

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.logo_preview = None
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Mijn Bedrijfs Instellingen", font=("Arial", 24, "bold")).pack(pady=20)
        
        ctk.CTkLabel(self, text="⚠️ Alleen klassieke Outlook wordt ondersteund!", text_color="red").pack(pady=5)

        frame = ctk.CTkFrame(self)
        frame.pack(padx=20, pady=10, fill="x")

        # Variabelen
        self.name_var = StringVar()
        self.address_var = StringVar()
        self.postal_var = StringVar()
        self.city_var = StringVar()
        self.phone_var = StringVar()
        self.email_var = StringVar()
        self.iban_var = StringVar()
        self.bic_var = StringVar()
        self.kvk_var = StringVar()
        self.btw_var = StringVar()
        self.logo_path_var = StringVar()
        self.terms_var = StringVar()
        self.payment_term_var = StringVar()
        self.mollie_key_var = StringVar()

        labels = ["Naam bedrijf", "Adres", "Postcode", "Plaats", "Telefoon", "E-mail", "IBAN", "BIC", "KvK", "BTW"]
        vars_ = [self.name_var, self.address_var, self.postal_var, self.city_var, self.phone_var, self.email_var,
                 self.iban_var, self.bic_var, self.kvk_var, self.btw_var]

        row = 0
        for label, var in zip(labels, vars_):
            ctk.CTkLabel(frame, text=label).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            ctk.CTkEntry(frame, textvariable=var, width=400).grid(row=row, column=1, padx=5, pady=5)
            row += 1

        # ===============================
        # Logo selectie
        # ===============================
        ctk.CTkLabel(frame, text="Logo").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        logo_frame = ctk.CTkFrame(frame)
        logo_frame.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        self.logo_entry = ctk.CTkEntry(logo_frame, textvariable=self.logo_path_var, width=300)
        self.logo_entry.pack(side="left", padx=(0,5))
        self.logo_button = ctk.CTkButton(logo_frame, text="Bladeren", command=self.select_logo)
        self.logo_button.pack(side="left")
        row += 1

        # Logo preview
        self.logo_preview_label = Label(self)
        self.logo_preview_label.pack(pady=10)

        # ===============================
        # Betalingstermijn (net onder logo)
        # ===============================
        ctk.CTkLabel(frame, text="Betalingstermijn (dagen)").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(frame, textvariable=self.payment_term_var, width=100).grid(row=row, column=1, padx=5, pady=5, sticky="w")
        row += 1

        # ===============================
        # Voorwaarden veld
        # ===============================
        ctk.CTkLabel(frame, text="Voorwaarden").grid(row=row, column=0, padx=5, pady=5, sticky="nw")
        self.terms_text = ctk.CTkTextbox(frame, width=400, height=120)
        self.terms_text.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        row += 1

        # Mollie API sleutel
        ctk.CTkLabel(frame, text="Mollie API sleutel").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(frame, textvariable=self.mollie_key_var, width=400, show="*").grid(row=row, column=1, padx=5, pady=5)
        row += 1

        # Opslaan knop
        ctk.CTkButton(self, text="Opslaan", command=self.save_settings).pack(pady=20)
        
        if not hasattr(self, "save_msg_label"):
            self.save_msg_label = ctk.CTkLabel(self, text="", text_color="green")
            self.save_msg_label.pack(pady=5)
       
        
        # Laad bestaande instellingen
        self.load_settings()

    def select_logo(self):
        file_path = filedialog.askopenfilename(title="Selecteer logo",
                                               filetypes=[("PNG bestanden", "*.png"), ("Alle bestanden", "*.*")])
        if file_path:
            self.logo_path_var.set(file_path)
            self.show_logo_preview(file_path)

    def show_logo_preview(self, path):
        if os.path.exists(path):
            img = Image.open(path)
            img.thumbnail((150, 150))
            tk_img = ImageTk.PhotoImage(img)
            self.logo_preview_label.config(image=tk_img)
            self.logo_preview_label.image = tk_img

    def load_settings(self):
        settings = get_settings()
        if settings: 
            self.name_var.set(settings.get("name", ""))
            self.address_var.set(settings.get("address", ""))
            self.postal_var.set(settings.get("postal", ""))
            self.city_var.set(settings.get("city", ""))
            self.phone_var.set(settings.get("phone", ""))
            self.email_var.set(settings.get("email", ""))
            self.iban_var.set(settings.get("iban",""))
            self.bic_var.set(settings.get("bic",""))
            self.kvk_var.set(settings.get("kvk", ""))
            self.btw_var.set(settings.get("btw", ""))
            self.logo_path_var.set(settings.get("logo_path", ""))
            self.terms_var.set(settings.get("terms", ""))
            self.payment_term_var.set(settings.get("payment_term_days", 14))
            if settings.get("logo_path") and os.path.exists(settings["logo_path"]):
                self.show_logo_preview(settings["logo_path"])
            if settings.get("mollie_api_key"):
                self.mollie_key_var.set(settings.get("mollie_api_key"))

            self.terms_text.delete("1.0", "end")
            self.terms_text.insert("1.0", settings.get("terms", ""))
                

    def save_settings(self):
        settings = get_settings() or {}
        data = {
            "name": self.name_var.get(),
            "address": self.address_var.get(),
            "postal": self.postal_var.get(),
            "city": self.city_var.get(),
            "phone": self.phone_var.get(),
            "email": self.email_var.get(),
            "iban": self.iban_var.get(),
            "bic": self.bic_var.get(),
            "kvk": self.kvk_var.get(),
            "btw": self.btw_var.get(),
            "logo_path": self.logo_path_var.get(),
            "logo_width": 40,
            "logo_height": 20,
            "terms": self.terms_text.get("1.0", "end").strip(),
            "payment_term_days": int(self.payment_term_var.get()),
            "mollie_api_key": self.mollie_key_var.get(),
        }
        save_settings(data)

        # ✅ Maak de boodschap in het midden van het scherm
        if hasattr(self, "_msg_label") and self._msg_label.winfo_exists():
            self._msg_label.destroy()  # verwijder oude label als die er nog is

        self._msg_label = ctk.CTkLabel(self, text="Instellingen opgeslagen!", font=("Arial", 18, "bold"), text_color="green")
        self._msg_label.place(relx=0.5, rely=0.5, anchor="center")

        # ✅ Fade-out functie
        def fade(step=0):
            colors = ["#00aa00", "#33bb33", "#66cc66", "#99dd99", "#ccffaa", "#ffffff"]  # van groen naar wit
            if step < len(colors):
                self._msg_label.configure(text_color=colors[step])
                self.after(300, lambda: fade(step + 1))
            else:
                self._msg_label.destroy()

        fade()