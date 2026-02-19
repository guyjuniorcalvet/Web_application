"""
Moteur de taxes pour calculer les taxes applicables selon la province de livraison.
"""

TAX_RATES = {
    'QC': 0.15,  # Québec: 15%
    'ON': 0.13,  # Ontario: 13%
    'AB': 0.05,  # Alberta: 5%
    'CB': 0.12,  # Colombie-Britannique: 12%
    'NE': 0.14,  # Nouvelle-Écosse: 14%
}
# Fonction pour obtenir le taux de la taxe selon la province
def get_tax_rate(province):
    if province not in TAX_RATES:
        raise ValueError(f"Province '{province}' non reconnue. Provinces valides: {list(TAX_RATES.keys())}")
    return TAX_RATES[province]


# Fonction pour calculer le montant de la taxe 
def calculate_taxes(subtotal, province):
    tax_rate = get_tax_rate(province)
    tax_amount = round(subtotal * tax_rate, 2)
    return tax_amount


# Fonction pour calculer le montant total incluant les taxes 
def calculate_total_with_tax(subtotal, province):
    
    tax_amount = calculate_taxes(subtotal, province)
    total_price_tax = round(subtotal + tax_amount, 2)
    return total_price_tax