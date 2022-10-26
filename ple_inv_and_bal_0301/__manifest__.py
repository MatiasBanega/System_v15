{
    'name': 'Formato 3.1 Libro de Inventarios y Balances - Estado de Situación Financiera',
    'version': '15.0.3.0.2',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'summary': 'This module creates the format 3.1 "Statement of financial position" of the electronic inventory and balance book.',
    'category': 'Accounting',
    'depends': ['ple_sale_book'],
    'data': [
        'eeff_ple.sql',
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/eeff_ple_views.xml',
        'views/ple_inv_bal_views.xml',
        'views/ple_inv_bal_initial_balances.xml',
        'reports/ple_inv_bal_report.xml',
        'reports/ple_inv_bal_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 35.00
}
