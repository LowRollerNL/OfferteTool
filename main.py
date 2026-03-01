import sys
import os
import socket
import win32gui
import win32con
import requests
import tempfile
from config import APP_VERSION
from models import init_db, init_settings, migrate_settings_table
import customtkinter as ctk
from config import COMPANY

GITHUB_API_URL = "https://api.github.com/repos/<gebruiker>/<repo>/releases/latest"
APP_VERSION = "1.0"  # jouw huidige versie

# ===============================
# PyInstaller-proof pad handling
# ===============================
if getattr(sys, "frozen", False):
    # Als exe via PyInstaller
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Helper functie voor assets / pdf / database
def resource_path(relative_path):
    """Geeft het juiste pad, werkt voor exe en script"""
    return os.path.join(BASE_DIR, relative_path)

# Database pad
DB_PATH = resource_path("offerte.db")

# ===============================
# Database initialisatie
# ===============================
init_db()
init_settings()
migrate_settings_table()

# ===============================
# UI imports
# ===============================
from ui.dashboard import DashboardView
from ui.item_manager import ItemManager
from ui.new_document import NewDocumentView
from ui.overview import OverviewView
from ui.settings import SettingsView
from ui.customer_manager import CustomerManagerView
from ui.year_overview import YearOverview

# ===============================
# Single-instance check (Windows)
# ===============================
def is_already_running(port=65432):
    """Controleer of een andere instantie al draait via TCP socket"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        s.listen(1)
        return False, s  # geen andere instantie
    except socket.error:
        return True, None  # app draait al

def bring_existing_window_to_front(title_contains="OFT"):
    """Zet bestaand venster met titel in focus"""
    def enum_windows(hwnd, result):
        if win32gui.IsWindowVisible(hwnd) and title_contains in win32gui.GetWindowText(hwnd):
            result.append(hwnd)
    hwnds = []
    win32gui.EnumWindows(enum_windows, hwnds)
    if hwnds:
        hwnd = hwnds[0]
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)

# ===============================
# Check op meerdere instanties
# ===============================
already_running, sock = is_already_running()
if already_running:
    bring_existing_window_to_front(title_contains="OFT")  # past bij jouw window.title
    sys.exit()  # sluit tweede instantie

# ===============================
# App Class
# ===============================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OFT")
        # self.state("zoomed")  # start fullscreen
        self.minsize(1000,800)  # weg, niet nodig

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.create_layout()

    # ==========================
    # Layout
    # ==========================
    def create_layout(self):

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        # Bedrijfsnaam
        ctk.CTkLabel(
            self.sidebar,
            text=COMPANY["name"],
            font=("Arial", 18, "bold")
        ).pack(pady=(30, 20))

        # Navigatie knoppen
        self.dashboard_btn = ctk.CTkButton(
            self.sidebar,
            text="Dashboard",
            command=self.show_dashboard,
            height=40
        )
        self.dashboard_btn.pack(fill="x", padx=20, pady=5)

        self.offertes_btn = ctk.CTkButton(
            self.sidebar,
            text="Offertes",
            command=self.show_offertes,
            height=40
        )
        self.offertes_btn.pack(fill="x", padx=20, pady=5)

        self.facturen_btn = ctk.CTkButton(
            self.sidebar,
            text="Facturen",
            command=self.show_facturen,
            height=40
        )
        self.facturen_btn.pack(fill="x", padx=20, pady=5)
        
        self.materialen_btn = ctk.CTkButton(
            self.sidebar,
            text="Itemlijst beheren",
            command=self.show_items,
            height=40
        )
       
        self.materialen_btn.pack(fill="x", padx=20, pady=5)
        

        #klanten bestand Knop
        self.customers_btn = ctk.CTkButton(
            self.sidebar,
            text="Klantenbestand",
            command=self.show_customers,
            height=40
        )
        self.customers_btn.pack(fill="x", padx=20, pady=5)

        
        # Instellingen knop
        self.instellingen_btn = ctk.CTkButton(
            self.sidebar,
            text="Mijn Bedrijf Instellingen",
            command=self.show_settings,
            height=40
        )
        self.instellingen_btn.pack(fill="x", padx=20, pady=5)
        
        self.jaaroverzicht_btn = ctk.CTkButton(
            self.sidebar,
            text="Jaaroverzicht",
            command=self.show_year_overview,
            height=40
        )
        self.jaaroverzicht_btn.pack(fill="x", padx=20, pady=5)

        # Spacer
        ctk.CTkLabel(self.sidebar, text="").pack(expand=True)

        # Footer
        ctk.CTkLabel(
            self.sidebar,
            text="v1.0",
            font=("Arial", 12)
        ).pack(pady=20)

        # Main content
        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        # Startscherm
        self.show_dashboard()

    # ==========================
    # Content management
    # ==========================
    def clear_content(self):
        """Verwijder alles uit content-frame"""
        for widget in self.content.winfo_children():
            widget.destroy()

    # ==========================
    # Navigatie functies
    # ==========================
    def show_dashboard(self):
        self.clear_content()
        DashboardView(self.content)

    def show_offertes(self):
        self.clear_content()
        OverviewView(self.content, "offerte")

    def show_facturen(self):
        self.clear_content()
        OverviewView(self.content, "factuur")
     
    def show_items(self):
        self.clear_content()
        ItemManager(self.content)  # plaats ItemManager inline in het content-frame    

    def show_settings(self):
        self.clear_content()
        SettingsView(self.content)  # settings view netjes in content-frame
        
    def show_customers(self):
        self.clear_content()
        CustomerManagerView(self.content)    
        
    def show_year_overview(self):
        self.clear_content()
        from ui.year_overview import YearOverview  # nieuw component
        YearOverview(self.content)    
            

def check_for_update_ctk(parent):
    """Controleer GitHub voor nieuwe release en toon CustomTkinter popup"""
    try:
        resp = requests.get(GITHUB_API_URL, timeout=5)
        resp.raise_for_status()
        release = resp.json()
        latest_version = release["tag_name"].lstrip("v")

        if latest_version != APP_VERSION:
            assets = release.get("assets", [])
            exe_asset = next((a for a in assets if a["name"].endswith(".exe")), None)
            
            if exe_asset:
                # Maak popup frame
                popup = ctk.CTkToplevel(parent)
                popup.title("Update beschikbaar")
                popup.geometry("400x200")
                popup.grab_set()  # focus op popup

                msg = f"Er is een nieuwe versie beschikbaar: {latest_version}\n\nWil je deze downloaden en installeren?"
                label = ctk.CTkLabel(popup, text=msg, wraplength=380, justify="center")
                label.pack(pady=20, padx=10)

                # Knop acties
                def download_update():
                    url = exe_asset["browser_download_url"]
                    tmp_file = os.path.join(tempfile.gettempdir(), exe_asset["name"])
                    try:
                        with requests.get(url, stream=True) as r:
                            r.raise_for_status()
                            with open(tmp_file, "wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        os.startfile(tmp_file)
                        parent.destroy()  # sluit oude app
                    except Exception as e:
                        error_popup = ctk.CTkToplevel(parent)
                        error_popup.title("Fout")
                        ctk.CTkLabel(error_popup, text=f"Download mislukt: {e}").pack(pady=10, padx=10)

                def cancel_update():
                    popup.destroy()

                # Knoppen
                btn_frame = ctk.CTkFrame(popup)
                btn_frame.pack(pady=10)
                ctk.CTkButton(btn_frame, text="Download & Installeer", command=download_update).pack(side="left", padx=10)
                ctk.CTkButton(btn_frame, text="Later", command=cancel_update).pack(side="right", padx=10)

                popup.mainloop()
                return True
        return False
    except Exception as e:
        print("Update check mislukt:", e)
        return False


# ==========================
# Start App
# ==========================
if __name__ == "__main__":
    app = App()
    check_for_update_ctk(app)
    app.mainloop()