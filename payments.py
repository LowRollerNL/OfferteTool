from mollie.api.client import Client
from models import get_settings, update_document

def generate_payment_link(self, doc):
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