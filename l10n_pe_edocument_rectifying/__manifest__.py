{
    'name': 'l10n_pe - Efact rectifying',
    'version': '15.0.1.1.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'summary': 'Efact rectifying',
    'category': 'Accounting',
    'depends': [
        'l10n_pe_edocument',
        'account_origin_invoice'
    ],
    'data': [
        'data/2.1/edi_templates.xml',
        'views/account_move_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 250.00
}
