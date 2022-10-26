{
    'name': 'Electronic Journal Perú',
    'version': '15.0.2.3.1',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co/ple',
    'summary': 'Generate Electronic Journal for PLE SUNAT',
    'description': """
        It generates the electronic journal that is mandatory for companies that must keep complete accounting in Peru. 
        It is very easy, Odoo generates the .txt ready to download and present to SUNAT through the electronic book program (PLE).”
    """,
    'category': 'Accounting',
    'depends': [
        'ple_sale_book',
        'invoice_type_document',
    ],
    'data': [
        'data/queries_data.xml',
        'views/company_views.xml',
        'views/ple_diary_views.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 160.00
}
