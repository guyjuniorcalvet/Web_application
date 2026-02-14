"""
Moteur de taxes pour calculer les taxes applicables selon la province de livraison.
"""

TAX_RATES = {
    'QC': 0.15,  # Québec: 15%
    'ON': 0.13,  # Ontario: 13%
    'AB': 0.05,  # Alberta: 5%
    'BC': 0.12,  # Colombie-Britannique: 12%
    'NS': 0.14,  # Nouvelle-Écosse: 14%
}

#Fonction pour obtenir le taux de taxe selon la province
def get_tax_rate(province):
    if province not in TAX_RATES:
        raise ValueError(f"Province '{province}' non reconnue. Provinces valides: {list(TAX_RATES.keys())} ")
    
    return TAX_RATES[province]

#Fonction pour calculer le montant de la taxe
def calculate_taxes(total_price, province):
    tax_rate=get_tax_rate(province)
    tax_amount=int(total_price*tax_rate)
    return tax_amount

#Fonction pour calculer le montant total incluant les taxes
def calculate_total_with_tax(total_price, province):
    tax_amount=calculate_taxes(total_price,province)
    total_price_tax=total_price + tax_amount
    return total_price_tax