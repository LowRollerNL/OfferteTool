import customtkinter as ctk
from tkinter import StringVar

class YearOverview(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)

        # Kwartalen
        self.quarters = ["Q1", "Q2", "Q3", "Q4"]
        self.entries = {}  # opslag van variabelen per kwartaal

        for i, q in enumerate(self.quarters):
            frame = ctk.CTkFrame(self)
            frame.pack(fill="x", padx=5, pady=5)

            ctk.CTkLabel(frame, text=q, font=("Arial", 16, "bold")).grid(row=0, column=0, padx=5, pady=5)

            # Omzet incl. BTW
            sales_var = StringVar()
            ctk.CTkLabel(frame, text="Omzet incl. BTW:").grid(row=1, column=0, padx=5, pady=5)
            ctk.CTkEntry(frame, textvariable=sales_var).grid(row=1, column=1, padx=5, pady=5)

            # Inkoop excl. BTW
            purchase_var = StringVar()
            ctk.CTkLabel(frame, text="Inkoop excl. BTW:").grid(row=2, column=0, padx=5, pady=5)
            ctk.CTkEntry(frame, textvariable=purchase_var).grid(row=2, column=1, padx=5, pady=5)

            # BTW %
            btw_var = StringVar(value="21")
            ctk.CTkLabel(frame, text="BTW %:").grid(row=3, column=0, padx=5, pady=5)
            ctk.CTkEntry(frame, textvariable=btw_var).grid(row=3, column=1, padx=5, pady=5)

            # Tegel te betalen BTW
            result_var = StringVar(value="€ 0.00")
            btw_tile = ctk.CTkFrame(frame, fg_color="#e91e63", corner_radius=10, height=80)
            btw_tile.grid(row=0, column=2, rowspan=4, padx=10, pady=5)
            ctk.CTkLabel(btw_tile, text="Te betalen BTW", font=("Arial", 12, "bold")).pack(pady=(5,0))
            ctk.CTkLabel(btw_tile, textvariable=result_var, font=("Arial", 16, "bold")).pack(pady=5)

            # Opslaan in dictionary
            self.entries[q] = {
                "sales": sales_var,
                "purchase": purchase_var,
                "btw": btw_var,
                "result": result_var
            }

            # Bereken knop
            ctk.CTkButton(frame, text="Bereken", command=lambda q=q: self.calculate(q)).grid(row=4, column=0, columnspan=2, pady=5)

    def calculate(self, quarter):
        data = self.entries[quarter]
        try:
            sales_incl = float(data["sales"].get().replace(",", "."))
            purchase = float(data["purchase"].get().replace(",", "."))
            btw_percent = float(data["btw"].get().replace(",", "."))

            # Berekening omzet exclusief BTW
            sales_excl = sales_incl / (1 + btw_percent/100)
            btw_received = sales_incl - sales_excl

            # BTW betaald op inkoop
            btw_paid = purchase * (btw_percent / 100)

            # Netto te betalen BTW
            to_pay = round(btw_received - btw_paid, 2)
            data["result"].set(f"€ {to_pay:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        except ValueError:
            data["result"].set("Fout in invoer")