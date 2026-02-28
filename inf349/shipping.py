"""
Moteur de calculateur de prix de livraison selon le poids total de la commande
"""

def calculate_shipping_price(total_weight):

    if total_weight <= 0:
        raise ValueError("Le poids doit être supérieur à 0")
    
    # Tranche 1: Jusqu'à 500g
    if total_weight <= 500:
        return 5.0
    
    # Tranche 2: De 500g a moins de 2000g
    elif 500 < total_weight < 2000:
        return 10.0
    
    # Tranche 3: A partir de 2000g (2kg) et plus
    else:
        return 25.0
