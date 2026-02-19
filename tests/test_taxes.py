"""
Tests unitaires du moteur de taxes pour valider les calculs de taxes pour toutes les provinces
"""
import pytest
from inf349.taxes import get_tax_rate, calculate_taxes, calculate_total_with_tax

# Tests unitaires pour la méthode get_tax_rate()
class Test_get_tax_rate:
    
    # Test unitaire pour la fonctionnalité de la méthode get_tax_rate()
    def test_quebec_tax_rate(self):
        assert get_tax_rate('QC') == 0.15
    
    def test_ontario_tax_rate(self):
        assert get_tax_rate('ON') == 0.13
        
    def test_alberta_tax_rate(self):
        assert get_tax_rate('AB') == 0.05
        
    def test_colombie_britannique_tax_rate(self):
        assert get_tax_rate('CB') == 0.12
    
    def test_nouvelle_ecosse_tax_rate(self):
        assert get_tax_rate('NE') == 0.14

    # Test unitaire pour la gestion des erreurs 
    def test_invalid_province(self):
        with pytest.raises(ValueError):
            get_tax_rate('XX')

#Tests unitaires pour la méthode calculate_taxes()
class Test_calculate_taxes:
    
    #Test unitaire pour la fonctionnalité de la méthode calculate_taxes()
    def test_calculate_taxes_quebec(self):
        assert calculate_taxes(100.0, 'QC') == 15.0
        
    def test_calculate_taxes_ontario(self):
        assert calculate_taxes(100.0, 'ON') == 13.0
    
    def test_calculate_taxes_alberta(self):
        assert calculate_taxes(100.0, 'AB') == 5.0
    
    def test_calculate_taxes_colombie_britannique(self):
        assert calculate_taxes(100.0, 'CB') == 12.0

    def test_calculate_taxes_nouvelle_ecosse(self):
        assert calculate_taxes(100.0, 'NE') == 14.0
    
    # Test unitaire pour la gestion des erreurs et des exceptions
    def test_calculate_taxes_zero_subtotal(self):
        assert calculate_taxes(0.0, 'AB') == 0.0
    
    def test_calculate_taxes_invalid_province(self):
        with pytest.raises(ValueError):
            calculate_taxes(100.0, 'XX')
  

#Tests unitaires pour la méthode calculate_total_with_tax()
class Test_calculate_total_with_tax:
    
    
    
    #Test unitaire pour la fonctionnalité de la méthode calculate_total_with_tax()
    def test_total_with_tax_quebec(self):
        assert calculate_total_with_tax(100.0, 'QC') == 115.0
    
    def test_total_with_tax_ontario(self):
        assert calculate_total_with_tax(100.0, 'ON') == 113.0
    
    def test_total_with_tax_alberta(self):
        assert calculate_total_with_tax(100.0, 'AB') == 105.0
        
    def test_total_with_tax_colombie_britannique(self):
        assert calculate_total_with_tax(100.0, 'CB') == 112.0
    
    def test_total_with_tax_nouvelle_ecosse(self):
        assert calculate_total_with_tax(100.0, 'NE') == 114.0
    
    #Test unitaire pour la gestion des erreurs 
    def test_total_with_tax_zero_subtotal(self):
        assert calculate_total_with_tax(0.0, 'NE') == 0.0
    
    def test_total_with_tax_invalid_province(self):
        with pytest.raises(ValueError):
            calculate_total_with_tax(100.0, 'XX') 
   
    

