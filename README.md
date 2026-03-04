# Web_application

Application web e-commerce développée avec **Flask** dans le cadre du cours **INF349 – Technologies Web avancé**-INF349.

**Collaborateurs** : Guy Junior CALVET · Marie-Anne Randrianarivony · Paul Yvan SEKA

---

## Description du projet

Cette application permet de parcourir un catalogue de produits, de passer une commande (sélection de produit, quantité, informations de livraison) et d'effectuer un paiement en ligne via un service distant. Elle expose à la fois une **API REST** (JSON) et une **interface utilisateur** (HTML/CSS).

---

## Architecture et structure du projet

```
Web_application/
├── inf349/                  # Package principal Flask
│   ├── __init__.py          # Factory de l'app, modèles Peewee, routes API et UI
│   ├── app.py               # Point d'entrée WSGI
│   ├── taxes.py             # Moteur de calcul des taxes par province
│   ├── shipping.py          # Calculateur de frais de livraison par poids
│   ├── templates/           # Templates HTML (Jinja2)
│   │   ├── list_products.html
│   │   ├── order_form.html
│   │   ├── order_confirmation.html
│   │   └── payment_form.html
│   └── static/              # Fichiers statiques (CSS, images)
│       ├── styles.css
│       └── images/
├── tests/                   # Tests automatisés (pytest)
├── requirements.txt         # Dépendances Python
├── pytest.ini               # Configuration pytest
└── README.md
```

### Technologies utilisées

| Composant | Technologie |
|---|---|
| Framework web | Flask |
| ORM / Base de données | Peewee + SQLite |
| Templates | Jinja2 |
| Tests | pytest |
| CI | GitHub Actions |

---

## Fonctionnalités implémentées

### API REST

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/` | Liste des produits (JSON) |
| `GET` | `/api/products` | Liste des produits (JSON) |
| `POST` | `/order` | Création d'une commande (validation produit, quantité, stock) |
| `GET` | `/order/<id>` | Récupération du JSON complet d'une commande |
| `PUT` | `/order/<id>` | Mise à jour : informations client **ou** paiement par carte de crédit |

### Interface utilisateur (UI)

| Route | Description |
|---|---|
| `/ui/products` | Affichage du catalogue avec images, prix et état du stock |
| `/ui/order` | Formulaire d'achat (produit, quantité, courriel, adresse de livraison) |
| `/ui/order/<id>` | Confirmation de commande et récapitulatif du panier |
| `/ui/order/<id>/payment` | Formulaire de paiement sécurisé (carte de crédit) |

### Moteur de taxes

Calcul automatique des taxes selon la province de livraison :

| Province | Taux |
|---|---|
| Québec (QC) | 15 % |
| Ontario (ON) | 13 % |
| Alberta (AB) | 5 % |
| Colombie-Britannique (BC) | 12 % |
| Nouvelle-Écosse (NS) | 14 % |

### Calculateur de livraison

Frais de livraison calculés selon le poids total de la commande :

| Poids | Frais |
|---|---|
| ≤ 500 g | 5 $ |
| 500 g – 2 kg | 10 $ |
| ≥ 2 kg | 25 $ |

### Paiement

- Intégration avec le service de paiement distant (`POST /shops/pay/`)
- Validation complète des champs de carte de crédit (nom, numéro, expiration, CVV)
- Gestion des erreurs : carte refusée (`card-declined`), double paiement (`already-paid`), champs manquants
- Les informations client doivent être renseignées avant le paiement

### Gestion des erreurs

- Handler global pour les erreurs HTTP 422 (champs manquants, produit hors inventaire)
- Codes d'erreur normalisés : `missing-fields`, `out-of-inventory`, `already-paid`, `card-declined`

### Initialisation de la base de données

- Commande `flask init-db` pour créer les tables et importer les produits depuis le service distant
- Chargement automatique des produits au premier lancement de l'application

### Design responsive

- CSS responsive pour une navigation adaptée aux différents appareils

---

## Modèles de données (Peewee)

- **Product** : `id`, `name`, `description`, `price`, `in_stock`, `weight`, `image`
- **Order** : `id`, `product_id`, `quantity`, `total_price`, `shipping_price`, `total_price_tax`, informations client (email, adresse), informations de paiement (carte de crédit, transaction)

---

## Backlog du projet (Issues)

### Issues fermées (22/23)

| # | Titre | Description |
|---|---|---|
| 1 | Formulaire Achat | Interface pour sélectionner la quantité et valider le panier |
| 2 | Calculateur Livraison | Calcul selon poids (5$ si ≤500g, 10$ si <2kg, 25$ si ≥2kg) |
| 3 | Gestion Erreurs | Handler global pour les erreurs 422 |
| 4 | Init-DB | Implémenter la commande `flask init-db` pour SQLite |
| 5 | Client Paiement | Intégration `POST /shops/pay/` vers le service de l'enseignant |
| 6 | Gestion Erreurs | Handler global pour les erreurs 422 (missing-fields, out-of-inventory) |
| 7 | Modèles Peewee | Création des classes Product, Order, Customer, Transaction |
| 8 | POST /order | Création de commande (validation ID produit, quantité et stock) |
| 9 | GET /order/\<id\> | Route pour récupérer le JSON complet d'une commande |
| 10 | PUT /order/\<id\> (Client) | Route pour ajouter email et infos de livraison à une commande |
| 11 | Moteur de Taxes | Calcul selon province (QC: 15%, ON: 13%, AB: 5%, BC: 12%, NS: 14%) |
| 12 | Client Produits | Script fetch GET /products.json au lancement (persistance locale) |
| 13 | Validation Paiement | Empêcher le double paiement et gérer card-declined |
| 14 | Liste de Produits | Affichage des produits avec images, prix et état du stock |
| 15 | Formulaire Livraison | Saisie des infos client (Email, Adresse, Ville, Province) |
| 16 | Interface Paiement | Formulaire sécurisé pour les infos de carte de crédit |
| 17 | Design Responsive | CSS pour rendre l'application web responsive |
| 18 | Initialisation Flask | Set-up du projet, création des dossiers static/templates et app.py |
| 19 | Modèles de données Peewee | Product, Order, ShippingInfo, Transaction |
| 20 | Client Produits | Script fetch (GET products.json) au lancement (persistance locale) |
| 21 | Init-DB | Implémentation de la commande `flask init-db` pour SQLite |
| 22 | Interface Liste de produits | Amélioration de l'interface et ajout des images des produits |

### Issue ouverte (1/23)

| # | Titre | Description |
|---|---|---|
| 23 | Rédaction du rapport final | Synthèse des rapports de session, backlogs et captures d'écran |

---

## Chronologie du développement

| Date | Étape clé |
|---|---|
| 9 fév. 2026 | Création du dépôt, fichiers de base, plan de projet et backlogs |
| 11 fév. 2026 | API `POST /order`, `GET /order/<id>`, `PUT /order/<id>`, formulaire d'achat et confirmation |
| 14 fév. 2026 | Moteur de taxes et calculateur de livraison |
| 17 fév. 2026 | Formulaire d'achat complet avec gestion d'erreurs |
| 19 fév. 2026 | Tests unitaires (taxes, livraison) |
| 21 fév. 2026 | Intégration du service de paiement distant |
| 23 fév. 2026 | Affichage de la liste des produits |
| 26 fév. 2026 | Mise en place de GitHub Actions (CI) |
| 27 fév. 2026 | Ajout des images produits, formulaire de paiement, conformité provinces |
| 28 fév. 2026 | Tests API complets, séparation client/paiement, design responsive, validation paiement |
| 1 mars 2026 | Déploiement de l'application Flask |

---

## Contributions de l'équipe

| Membre | Contributions principales |
|---|---|
| **Guy Junior CALVET** | Architecture du projet, gestion du dépôt, formulaire d'achat, validation paiement, CI, déploiement |
| **Marie-Anne Randrianarivony** | Moteur de taxes, calculateur de livraison, intégration paiement, images produits, tests |
| **Paul Yvan SEKA** | Routes API (POST/GET/PUT order), tests API, formulaire de paiement, design responsive, corrections |

---

## Prérequis

- Python 3.10+

## Installation

```bash
pip install -r requirements.txt
```

## Initialiser la base de données

```bash
flask --app inf349 init-db
```

## Lancer l'application

```bash
flask --app inf349 run
```

En mode développement (avec rechargement automatique) :

```bash
flask --app inf349 run --debug
```

L'application sera disponible à l'adresse http://127.0.0.1:5000.

## Exécuter les tests

```bash
pytest
```

---

## Liens utiles

- [Issues / Backlog](https://github.com/guyjuniorcalvet/Web_application/issues)
- [Wiki (Plan de projet et rapports de session)](https://github.com/guyjuniorcalvet/Web_application/wiki)
