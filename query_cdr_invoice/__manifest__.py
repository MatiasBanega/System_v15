{
    'name': 'Query CDR invoice',
    'version': '15.0.2.1.1',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'summary': 'This module allows the consultation of the CDR in SUNAT and changes the status of the EDI Document to "Sent"',
    'category': 'Localization',
    "depends": [
        'l10n_pe_edocument',
        'qr_code_on_sale_invoice',
        'amount_to_text',
    ],
    'data': [
        'views/account_move_cdr.xml',
        'views/print_qr_and_quantity.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 125.00
}
