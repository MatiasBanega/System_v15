{
    'name': 'Account move date from stock',
    'version': '15.0.0.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'live_test_url': 'https://www.ganemo.co',
    'category': 'Warehouse',
    'description': """
It allows you to enter an "effective date" of the transfer that will be taken to register the delivery voucher, instead of the date when it is validated.
Without this module, Odoo always takes the validation date. It also creates the "accounting date" field in the "Stock Movements" and in the "Product Movements".
The "effective date" is used to post the journal entries related to the warehouse directory. It also creates the "accounting date" field in the "Product 
Valuation" and auto-completes with the effective date. When converting valuation into foreign currency, Odoo will take the effective (accounting) date and not 
the creation date.
    """,
    'depends': [
        'change_stock_movement_date',
        'purchase_stock'
    ],
    'data': ['views/stock_valuation_layer_views.xml'],
    'installable': True,
    'active': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.00
}
