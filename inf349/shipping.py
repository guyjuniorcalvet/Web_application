"""
Moteur de calculateur de prix de livraison selon le poids total de la commande
"""
# Prix de la livraison selon les tranches de poids (poids en grammes, prix en dollars)
SHIPPING = [
    (500, 5.0),          # Jusqu'à 500g: 5.00$
    (2000, 10.0),        # 500g à 2kg: 10.00$
    (float('inf'), 25.0) # 2kg et plus: 25.00$
]

#Fonction pour calculer le prix de la livraison selon le poids 
def calculate_shipping_price(total_weight):
    
    if total_weight <= 0:
        raise ValueError("Le poids doit être supérieur à 0")

    for max_weight, price in SHIPPING:
        if total_weight <= max_weight:
            return round(float(price), 2)

    # Should never reach here, but just in case
    return round(float(SHIPPING[-1][1]), 2)