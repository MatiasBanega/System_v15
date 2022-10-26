{
    'name': 'Accounting ledger PLE - SUNAT (Perú)',
    'version': '15.0.2.4.1',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co/ple',
    'summary': 'Accounting ledger PLE - SUNAT (Perú)',
    'description': """
        It generates the electronic ledger that is mandatory for companies that must keep complete accounting in Peru.
        It is very easy, Odoo generates the .txt ready to download and present to SUNAT through the electronic book program (PLE).
    """,
    'category': 'Accounting',
    'depends': [
        'ple_sale_book',
        'invoice_type_document',
    ],
    'data': [
        'views/ple_ledger_views.xml',
        'data/queries_data.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 160.00
}
