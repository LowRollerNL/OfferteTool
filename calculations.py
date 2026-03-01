def calculate_sale_price(purchase_price, profit_percent):
    return purchase_price + (purchase_price * profit_percent / 100)

def calculate_line_total(quantity, sale_price):
    return quantity * sale_price

def calculate_btw(amount, btw_percent):
    return amount * btw_percent / 100

def calculate_totals(lines):
    total_excl = sum(line["total"] for line in lines)
    total_btw = sum(line["btw_amount"] for line in lines)
    total_incl = total_excl + total_btw

    return total_excl, total_btw, total_incl