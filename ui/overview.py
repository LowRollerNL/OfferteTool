import customtkinter as ctk
import os
import webbrowser
import urllib.parse
import uuid
import win32com.client

from models import (
    get_documents,
    delete_document,
    get_document_lines,
    create_document,
    add_document_line,
    update_document,
    get_customers,
    get_settings
)

from ui.new_document import NewDocumentView
from pdf_generator import generate_offerte_pdf
from mollie.api.client import Client
from payments import generate_payment_link


class OverviewView(ctk.CTkFrame):

    def __init__(self, parent, doc_type):
        super().__init__(parent)
        self.doc_type = doc_type
        self.pack(fill="both", expand=True)
        self.build()

    # ==========================
    # UI
    # ==========================
    def build(self):
        # Mapping voor nette labels
        DOC_TYPE_LABELS = {
            "factuur": "Facturen",
            "offerte": "Offertes",
            "klant": "Klantenbestand"
        }

        display_name = DOC_TYPE_LABELS.get(self.doc_type, self.doc_type)

        ctk.CTkLabel(
            self,
            text=f"Overzicht {display_name}",
            font=("Arial", 24, "bold")
        ).pack(pady=20)

        ctk.CTkButton(
            self,
            text=f"Nieuwe {display_name[:-1]}",  # Verwijder de 'n' bij 'Facturen' → 'Factuur'
            command=self.create_new
        ).pack(pady=10)

        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.load_data()


    # Data laden (aangepast voor facturen open/betaald splitsing)
    # ==========================
    def load_data(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        documents = get_documents(self.doc_type)
        customers_dict = {c["id"]: c["name"] for c in get_customers()}

        if self.doc_type == "factuur":
            not_paid_docs = []
            paid_docs = []

            for d in documents:
                # Bestaande status of Mollie-status
                status = d["payment_status"] or "open"
                if d["payment_id"]:  # als er een payment_id is
                    status = self.refresh_payment_status(d)

                if status == "paid":
                    paid_docs.append(d)
                else:
                    not_paid_docs.append(d)

            # Sorteer beide groepen DESC op factuurnummer
            not_paid_docs = sorted(not_paid_docs, key=lambda d: d["number"], reverse=True)
            paid_docs = sorted(paid_docs, key=lambda d: d["number"], reverse=True)

            # ==========================
            # Header
            # ==========================
            header = ctk.CTkFrame(self.list_frame)
            header.pack(fill="x", pady=(5, 10))
            ctk.CTkLabel(header, text="Nr", width=100, anchor="w").pack(side="left", padx=(5,0))
            ctk.CTkLabel(header, text="Klant", width=220, anchor="w").pack(side="left")
            ctk.CTkLabel(header, text="Datum", width=110, anchor="w").pack(side="left")
            ctk.CTkLabel(header, text="Bedrag", width=120, anchor="e").pack(side="left")

            # ==========================
            # Niet-betaalde facturen bovenaan
            # ==========================
            for doc in not_paid_docs:
                self._render_factuur_row(doc, customers_dict, open_section=True)

            # ==========================
            # Betaalde facturen onderaan
            # ==========================
            if paid_docs:
                spacer = ctk.CTkFrame(self.list_frame, height=20)
                spacer.pack()

                # Label boven de paid-sectie
                ctk.CTkLabel(
                    self.list_frame,
                    text="Betaalde facturen ↓",
                    font=("Arial", 16, "bold"),
                    text_color="green",
                    anchor="center"
                ).pack(fill="x", padx=5, pady=(0,5))

                for doc in paid_docs:
                    self._render_factuur_row(doc, customers_dict, open_section=False)

        else:
            # ==========================
            # Offertes gewoon zoals voorheen
            # ==========================
            documents_sorted = sorted(documents, key=lambda d: d["number"], reverse=True)

            # Header maken zoals bij facturen
            header = ctk.CTkFrame(self.list_frame)
            header.pack(fill="x", pady=(5, 10))
            ctk.CTkLabel(header, text="Nr", width=100, anchor="w").pack(side="left", padx=(5,0))
            ctk.CTkLabel(header, text="Klant", width=220, anchor="w").pack(side="left")
            ctk.CTkLabel(header, text="Datum", width=110, anchor="w").pack(side="left")
            ctk.CTkLabel(header, text="Bedrag", width=120, anchor="e").pack(side="left")

            for doc in documents_sorted:
                self._render_factuur_row(doc, customers_dict, open_section=True)
                                
    # ==========================
    # Factuur / offerte rij renderen
    # ==========================
    def _render_factuur_row(self, doc, customers_dict, open_section=True):
        row = ctk.CTkFrame(self.list_frame)
        row.pack(fill="x", pady=3)

        total_incl = doc["total_incl"]
        customer_name = customers_dict.get(doc["customer_id"], "Onbekend")

        # =========================
        # KOLOMMEN
        # =========================

                    
        # ==========================
        # Verstuurd label (initieel leeg)
        # ==========================

        # Factuurnummer
        ctk.CTkLabel(
            row,
            text=doc["number"][:9],
            width=100,
            anchor="w"
        ).pack(side="left", padx=(5, 0))

        # Klantnaam
        ctk.CTkLabel(
            row,
            text=customer_name[:20],
            width=220,
            anchor="w"
        ).pack(side="left")

        # Datum
        ctk.CTkLabel(
            row,
            text=doc["date"],
            width=110,
            anchor="w"
        ).pack(side="left")

        # Bedrag (rechts uitlijnen!)
        ctk.CTkLabel(
            row,
            text=f"€ {total_incl:.2f}",
            width=120,
            anchor="e"
        ).pack(side="left", padx=(0, 20))

        # =========================
        # KNOPPEN
        # =========================

        ctk.CTkButton(
            row,
            text="Bewerken",
            width=90,
            command=lambda d=doc: self.edit_document(d["id"])
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            row,
            text="PDF",
            width=70,
            command=lambda d=doc: self.save_pdf(d)
        ).pack(side="left", padx=3)

        if doc.get("is_sent") == 1:
            send_btn = ctk.CTkButton(row, text="Verstuurd", fg_color="green")
        else:
            send_btn = ctk.CTkButton(row, text="Versturen", width=90)
            send_btn.configure(command=lambda d=doc, b=send_btn: self.send_pdf(d, b))
        send_btn.pack(side="left", padx=3)

        ctk.CTkButton(
            row,
            text="Verwijderen",
            width=100,
            fg_color="red",
            hover_color="#cc0000",
            command=lambda d=doc: self.delete_document(d["id"])
        ).pack(side="left", padx=3)
   

        # ==========================
        # Facturen
        # ==========================
        if self.doc_type == "factuur":

            from datetime import datetime

            status = doc["payment_status"] or "open"

            # Als er een payment_id is → status verversen bij Mollie
            if doc["payment_id"]:
                status = self.refresh_payment_status(doc)

            color_map = {
                "open": "orange",
                "paid": "green",
                "failed": "red",
                "canceled": "gray",
                "expired": "darkred",
                "pending": "orange",
                "authorized": "blue"
            }

            # Status label tonen
            ctk.CTkLabel(
                row,
                text=status.capitalize(),
                text_color=color_map.get(status, "white")
            ).pack(side="left", padx=10)

            # ==========================
            # Countdown tonen (alleen als nog niet betaald)
            # ==========================
            if status != "paid" and doc["due_date"]:  # due_date aanwezig
                due_date = datetime.strptime(doc["due_date"], "%Y-%m-%d")
                remaining_days = (due_date - datetime.now()).days

                if remaining_days >= 0:
                    countdown_text = f"{remaining_days} dagen resterend"
                    countdown_color = "white"
                else:
                    countdown_text = f"Overschreden met {abs(remaining_days)} dagen"
                    countdown_color = "red"

                ctk.CTkLabel(
                    row,
                    text=countdown_text,
                    text_color=countdown_color
                ).pack(side="left", padx=10)
        # ==========================
        # Offertes
        # ==========================
        if self.doc_type == "offerte":
            if doc["is_invoiced"] == 0:
                btn = ctk.CTkButton(row, text="Maak factuur", command=lambda d=doc, r=row: self.create_invoice(d, r))
            else:
                btn = ctk.CTkButton(row, text="Factuur gemaakt", fg_color="green", state="disabled")
            btn.pack(side="left", padx=5)

    # ==========================
    # PDF Opslaan
    # ==========================
    def save_pdf(self, doc):
        customer = [c for c in get_customers() if c["id"] == doc["customer_id"]][0]
        pdf_path = generate_offerte_pdf(doc, customer)
        os.startfile(pdf_path)

    # ==========================
    # Betaallink genereren
    # ==========================
    def generate_payment_link(self, doc):

        settings = get_settings()
        mollie_key = settings.get("mollie_api_key")

        if not mollie_key:
            print("Geen Mollie API sleutel ingesteld")
            return None

        client = Client()
        client.set_api_key(mollie_key)

        payment = client.payments.create({
            "amount": {
                "currency": "EUR",
                "value": f"{doc["total_incl"]:.2f}"
            },
            "description": f"Factuur {doc["number"]}",
            "redirectUrl": "https://jouwdomein.nl/bedankt",
            "webhookUrl": "https://jouwdomein.nl/webhook",
            "metadata": {
                "invoice_id": doc["id"]
            }
        })

        update_document(doc["id"], {
            "payment_id": payment.id,
            "payment_url": payment.checkout_url,
            "payment_status": payment.status
        })

        return payment.checkout_url
    # ==========================
    # PDF Versturen
    # ==========================
    # ==========================
# PDF Versturen (compatibel nieuwe Outlook)
# ==========================
    def send_pdf(self, doc, button=None):
        import win32com.client
        import win32gui
        import win32con
        import time
        import webbrowser
        import urllib.parse
        from models import get_customers, get_settings, update_document
        from pdf_generator import generate_offerte_pdf

 
        update_document(doc["id"], {"is_sent": 1})  # i.p.v. "status": "verstuurd"

        if button:
            button.configure(
                text="Verstuurd",
                fg_color="green",
                hover_color="#0f8f0f"
            )

        # Klant en PDF
        customer = [c for c in get_customers() if c["id"] == doc["customer_id"]][0]
        pdf_path = generate_offerte_pdf(doc, customer)
        email_address = customer[2]

        company_info = get_settings()

        # Basis aanhef en afsluitende groet
        body_intro = f"Beste {customer[1]},\n\nBijgaand ontvangt u de {self.doc_type}.\n\n"
        body_footer = f"\nMet vriendelijke groet,\n{company_info['name']}"

        # Mail body samenstellen
        if self.doc_type == "factuur":
            settings = get_settings()
            payment_url = doc.get("payment_url", None)
            payment_id = doc.get("payment_id", None)

            if settings.get("mollie_api_key") and not payment_url:
                payment_url = self.generate_payment_link(doc)

            iban = settings.get("iban", "")
            company_name = settings.get("name", "")

            body = (
                body_intro +
                "U kunt de factuur eenvoudig voldoen via de volgende betaalpagina:\n\n" +
                (f"{payment_url}\n\n" if payment_url else "") +
                "Indien u liever via bankoverschrijving betaalt, dan kan dat ook.\n\n" +
                f"IBAN: {iban}\n"
                f"T.n.v.: {company_name}\n"
                f"Onder vermelding van factuur {doc["number"]}.\n\n" +
                body_footer
            )
        else:
            body = (
                body_intro +
                "Wanneer u akkoord gaat, verzoek ik u vriendelijk om de bijlage ondertekend aan ons te retourneren.\n\n" +
                "Mocht u vragen hebben of iets willen bespreken, dan hoor ik dat graag.\n\n" +
                body_footer
            )

        # ==========================
        # Probeer Outlook te gebruiken
        # ==========================
        try:
            outlook = win32com.client.gencache.EnsureDispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.To = email_address
            mail.Subject = f"{self.doc_type.capitalize()} {doc["number"]}"
            mail.Body = body
            mail.Attachments.Add(pdf_path)
            mail.Display()

            # Breng Outlook venster naar voorgrond
            time.sleep(0.3)  # korte pauze zodat venster zichtbaar is
            hwnd = win32gui.FindWindow(None, mail.Subject)
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)

        # ==========================
        # Fallback: mailto voor nieuwe Outlook / web Outlook
        # ==========================
        except Exception as e:
            print("Outlook niet beschikbaar, gebruik fallback mailto. Error:", e)
            subject = urllib.parse.quote(f"{self.doc_type.capitalize()} {doc["number"]}")
            body_encoded = urllib.parse.quote(body)
            webbrowser.open(f"mailto:{email_address}?subject={subject}&body={body_encoded}")
            print("Mail geopend via browser/mailto. Voeg PDF handmatig toe.")

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
        
               
    # ==========================
    # Offerte → Factuur
    # ==========================
    def create_invoice(self, doc, row):

        new_doc_id = create_document({
            "type": "factuur",
            "number": f"F-{doc["number"]}",
            "date": doc["date"],
            "due_date": doc["due_date"],
            "customer_id": doc["customer_id"],
            "status": "open",
            "total_excl": doc["total_excl"],
            "total_btw": doc["total_btw"],
            "total_incl": doc["total_incl"],
            "is_invoiced": 0
        })

        lines = get_document_lines(doc["id"])

        for line in lines:
            add_document_line(new_doc_id, {
                "description": line[2],
                "quantity": line[3],
                "purchase_price": line[4],
                "sale_price": line[5],
                "profit_percent": line[6],
                "btw_percent": line[7],
                "total": line[8]
            })

        update_document(doc["id"], {"is_invoiced": 1})

        # Knop groen maken
        for widget in row.winfo_children():
            if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "Maak factuur":
                widget.configure(text="Factuur gemaakt", fg_color="green", state="disabled")

        # Automatisch naar Facturen tegel navigeren
        app = self.master
        while app and not hasattr(app, "facturen_btn"):
            app = getattr(app, "master", None)

        if app and hasattr(app, "facturen_btn"):
            app.facturen_btn.invoke()  # activeert show_facturen()       

    # ==========================
    # Navigatie
    # ==========================
    def create_new(self):
        self.destroy()
        NewDocumentView(self.master, self.doc_type)

    def edit_document(self, document_id):
        self.destroy()
        NewDocumentView(self.master, self.doc_type, document_id=document_id)

    def delete_document(self, document_id):
        delete_document(document_id)
        self.load_data()

    def mark_as_paid(self, doc):
        update_document(doc["id"], {"is_paid": 1})
        self.load_data()
        
    def refresh_payment_status(self, doc):
        from mollie.api.client import Client
        from models import get_settings, update_document

        settings = get_settings()
        api_key = settings.get("mollie_api_key")

        if not api_key or not doc["payment_url"]:  # payment_id index
            return doc["payment_status"]  # bestaande status

        client = Client()
        client.set_api_key(api_key)

        payment = client.payments.get(doc["payment_id"])

        update_document(doc["id"], {
            "payment_status": payment.status
        })

        return payment.status    
            
        