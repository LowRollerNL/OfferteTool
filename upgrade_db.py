import requests
import tempfile
import os
import sys
import customtkinter as ctk
from config import APP_VERSION

GITHUB_API_URL = "https://api.github.com/repos/<gebruiker>/<repo>/releases/latest"

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
                        # Start installer
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