import customtkinter as ctk
from datetime import datetime
from models import get_documents, get_customers
from payments import generate_payment_link
from ui.customer_manager import open_customer_popup


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.build_dashboard()

    def build_dashboard(self):
        # Titel Dashboard
        ctk.CTkLabel(self, text="Dashboard", font=("Arial", 28, "bold")).pack(pady=20)

        # =====================
        # Haal documenten en klanten
        # =====================
        facturen = get_documents("factuur")
        offertes = get_documents("offerte")

        # Klanten dictionary voor snelle lookup
        customers = get_customers()
        customers_dict = {c["id"]: c["name"] for c in customers}  # werkt nu

        # =====================
        # Facturen splitsen in open en betaald
        # =====================
        open_offertes = [o for o in offertes if o["is_invoiced"] == 0]  # is_invoiced? of iets anders
        open_facturen = [f for f in facturen if f.get("payment_status") != "paid"]
        paid_facturen = [f for f in facturen if f.get("payment_status") == "paid"]

        # Berekeningen
        total_open_amount = sum(f["total_incl"] for f in open_facturen)
        total_paid_amount = sum(f["total_incl"] for f in paid_facturen)
        total_btw = sum(f["total_btw"] for f in paid_facturen)
        total_offertes = len(open_offertes)
        open_count = len(open_facturen)
        paid_count = len(paid_facturen)

        # =====================
        # Tegels container
        # =====================
        tiles_frame = ctk.CTkFrame(self)
        tiles_frame.pack(padx=20, pady=10, fill="x")

        # Offertes tegel
        offerte_tile = ctk.CTkButton(
            tiles_frame,
            text=f"Offertes\n{total_offertes} open",
            font=("Arial", 20, "bold"),
            fg_color="#4caf50",
            hover_color="#45a049",
            corner_radius=10,
            height=120,
            command=lambda: self.go_to_overview("offerte")
        )
        offerte_tile.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        # Facturen tegel
        facturen_tile = ctk.CTkButton(
            tiles_frame,
            text=f"Facturen\nOpen: {open_count}\nBetaald: {paid_count}",
            font=("Arial", 20, "bold"),
            fg_color="#2196f3",
            hover_color="#1976d2",
            corner_radius=10,
            height=120,
            command=lambda: self.go_to_overview("factuur")
        )
        facturen_tile.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        # Openstaand bedrag tegel
        open_tile = ctk.CTkFrame(tiles_frame, fg_color="#ff9800", corner_radius=10, height=120)
        open_tile.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(open_tile, text="Openstaand bedrag", font=("Arial", 16, "bold")).pack(pady=(20,0))
        ctk.CTkLabel(open_tile, text=f"€ {total_open_amount:,.2f}", font=("Arial", 20, "bold")).pack(pady=5)

        # Betaald bedrag tegel
        paid_tile = ctk.CTkFrame(tiles_frame, fg_color="white", corner_radius=10, height=120)
        paid_tile.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(paid_tile, text="Betaald", font=("Arial", 16, "bold"), text_color="green").pack(pady=(20,0))
        ctk.CTkLabel(paid_tile, text=f"€ {total_paid_amount:.2f}", font=("Arial", 20, "bold"), text_color="green").pack(pady=5)

        # Te betalen BTW tegel
        btw_tile = ctk.CTkFrame(tiles_frame, fg_color="#e91e63", corner_radius=10, height=120)
        btw_tile.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(btw_tile, text="Te betalen BTW", font=("Arial", 16, "bold")).pack(pady=(20,0))
        ctk.CTkLabel(btw_tile, text=f"€ {total_btw:,.2f}", font=("Arial", 20, "bold")).pack(pady=5)

        # =====================
        # Overdue facturen
        # =====================
        today = datetime.now().date()
        overdue_docs = [f for f in open_facturen if f["due_date"] and datetime.strptime(f["due_date"], "%Y-%m-%d").date() < today]

        overdue_frame = ctk.CTkFrame(self)
        overdue_frame.pack(fill="x", padx=20, pady=(20,10))

        ctk.CTkLabel(
            overdue_frame,
            text="💡 Facturen voorbij betalingstermijn",
            font=("Arial", 16, "bold"),
            text_color="red"
        ).pack(pady=(0,10))

        if overdue_docs:
            for doc in overdue_docs:
                row = ctk.CTkFrame(overdue_frame)
                row.pack(fill="x", pady=5)

                # Klantnaam ophalen via dictionary
                customer_name = customers_dict.get(doc["customer_id"], "Onbekend")

                ctk.CTkLabel(
                    row,
                    text=f"{doc["number"]:<10} | {customer_name:<20} | {doc["date"]:<10} | € {doc["total_incl"]:>9,.2f}",
                    text_color="red"
                ).pack(side="left", padx=5)

                ctk.CTkButton(
                    row,
                    text="Verstuur reminder",
                    fg_color="red",
                    hover_color="#cc0000",
                    command=lambda d=doc: self.send_reminder(d)
                ).pack(side="right", padx=5)
        else:
            ctk.CTkLabel(overdue_frame, text="Geen facturen voorbij betalingstermijn", text_color="white").pack(pady=5)

    # =====================
    # Navigatie naar overzicht
    # =====================
    def go_to_overview(self, doc_type):
        from ui.overview import OverviewView
        self.destroy()
        OverviewView(self.master, doc_type)

    # =====================
    # Reminder mail
    # =====================
    def send_reminder(self, doc):
        import win32com.client
        import win32con
        import win32gui
        import time
        from models import get_customers, get_settings
        from pdf_generator import generate_offerte_pdf
        
        # Klant ophalen
        customer = [c for c in get_customers() if c["id"] == doc["customer_id"]][0]
        pdf_path = generate_offerte_pdf(doc, customer)
        email_address = customer[2]

        settings = get_settings()
        iban = settings.get("iban", "")
        company_name = settings.get("name", "")
        mollie_key = settings.get("mollie_api_key")

        # Betaallink alleen gebruiken als API key bestaat
        payment_url = doc["payment_url"] if len(doc) > 13 else None

        if mollie_key:
            if not payment_url:
                payment_url = self.generate_payment_link(doc)
        else:
            payment_url = None  # Geen link als geen API key

        # Outlook mail object
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        recipient = mail.Recipients.Add(email_address)
        recipient.Type = 1  # 1 = To, 2 = CC, 3 = BCC
        mail.Subject = f"Betalingsherinnering – Factuur {doc["number"]}"

        # Body opbouwen
        body = (
            f"Beste {customer[1]},\n\n"
            f"Volgens onze administratie staat factuur {doc["number"]} nog open.\n"
            f"De vervaldatum van deze factuur was {doc["due_date"]}.\n\n"
            "Mogelijk is de betaling aan onze aandacht ontsnapt. "
            "Indien dit niet het geval is, verzoeken wij u vriendelijk het openstaande bedrag alsnog binnen 7 dagen te voldoen.\n\n"
        )

        # Betaallink alleen tonen als aanwezig
        if payment_url:
            body += (
                "U kunt de betaling eenvoudig uitvoeren via onderstaande betaallink:\n\n"
                f"{payment_url}\n\n"
            )

        body += (
            "Betaalt u liever via bankoverschrijving? Dan kunt u het factuurbedrag overmaken op:\n\n"
            f"IBAN: {iban}\n"
            f"T.n.v.: {company_name}\n"
            f"Onder vermelding van factuur {doc["number"]}.\n\n"
            "Indien uw betaling inmiddels is voldaan, kunt u deze herinnering als niet verzonden beschouwen.\n\n"
            f"Met vriendelijke groet,\n{company_name}"
        )

        mail.Body = body
        mail.Attachments.Add(pdf_path)
        mail.Display()

        time.sleep(0.5)

                # ===== Breng Outlook venster naar voorgrond =====
        time.sleep(0.1)  # korte pauze zodat venster zichtbaar is

        def bring_window_to_front(title_contains):
            def enum_windows(hwnd, result):
                if win32gui.IsWindowVisible(hwnd) and title_contains in win32gui.GetWindowText(hwnd):
                    result.append(hwnd)
            hwnds = []
            win32gui.EnumWindows(enum_windows, hwnds)
            if hwnds:
                hwnd = hwnds[0]
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)

        bring_window_to_front(mail.Subject)
        
    def generate_payment_link(self, doc):
        from models import get_settings, update_document
        from mollie.api.client import Client
        
        settings = get_settings()
        mollie_key = settings.get("mollie_api_key")

        # Als er geen Mollie API key is, gewoon terug None
        if not mollie_key:
            print("Geen Mollie API sleutel ingesteld – geen betaallink aangemaakt")
            return None

        # Mollie client alleen aanmaken als key aanwezig is
        from mollie.api.client import Client
        client = Client()
        client.set_api_key(mollie_key)

        payment = client.payments.create({
            "amount": {
                "currency": "EUR",
                "value": f"{doc["total_incl"]:.2f}"  # totaal bedrag
            },
            "description": f"Factuur {doc["number"]}",
            "redirectUrl": "https://jouwdomein.nl/bedankt",
            "webhookUrl": "https://jouwdomein.nl/webhook",
            "metadata": {
                "invoice_id": doc["id"]
            }
        })

        # Alleen updaten als betaal-link succesvol is aangemaakt
        if payment:
            update_document(doc["id"], {
                "payment_id": payment.id,
                "payment_url": payment.checkout_url,
                "payment_status": payment.status
            })
            return payment.checkout_url

        return None    