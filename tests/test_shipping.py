"""
Tests unitaires pour valider le calculateur de livraison
"""
import pytest
from inf349.shipping import calculate_shipping_price


class Test_calculate_shipping_price:
    
    # Test unitaire pour la fonctionnalité de la méthode calculate_shipping_price()
     def test_shipping_up_to_500g(self):
         assert calculate_shipping_price(400)==5.0
         
     def test_shipping_500g_to_2kg(self):
         assert calculate_shipping_price(800)==10.0
         
     def test_shipping_greater_than_2kg(self):
        assert calculate_shipping_price(3000)==25.0
    

    # Test unitaire pour le cas des limites de poids 
     def test_shipping_limite_500g(self):
        assert calculate_shipping_price(499) == 5.0
        assert calculate_shipping_price(500) == 5.0
        assert calculate_shipping_price(501) == 10.0
    
     def test_shipping_limite_2kg(self):
        assert calculate_shipping_price(1999) ==10.0
        assert calculate_shipping_price(2000) ==10.0
        assert calculate_shipping_price(2001) ==25.0
    
    # Test unitaire pour la gestion des erreurs et des exceptions
     def test_shipping_null_weight(self):
        with pytest.raises(ValueError):
            calculate_shipping_price(0)
 
     def test_shipping_negative_weight(self):
        with pytest.raises(ValueError):
            calculate_shipping_price(-100)
            