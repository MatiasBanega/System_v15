{
    'name': 'Change stock movement date',
    'version': '15.0.0.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'live_test_url': 'https://www.ganemo.co',
    'category': 'Warehouse',
    'description': """
It allows you to enter an "effective date" of the transfer that will be taken to register the delivery voucher, instead of the date when it is validated. 
Without this module, Odoo always takes the validation date. It also creates the "accounting date" field in the "Stock Movements" and in the "Product Movements. 
    """,
    'depends': ['stock'],
    'data': ['views/stock_picking_views.xml'],
    'installable': True,
    'active': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.00
}
