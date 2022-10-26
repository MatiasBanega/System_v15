{
    'name': 'Formato 3.1 Libro de Inventarios y Balances - Estado de situación financiera (Enterprise)',
    'version': '15.0.0.0.1',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'summary': 'This module creates the format 3.1 "Statement of financial position" of the electronic inventory and balance book (Enterprise).',
    'description': 'This module creates the format 3.1 "Statement of financial position" of the electronic inventory and balance book (Enterprise).',
    'category': 'Accounting',
    'depends': [
        'account_reports',
        'ple_inv_and_bal_0301',
        'ple_inv_and_bal_0320_ee',
    ],

    'data': [
        'security/ir.model.access.csv',
        'reports/ple_inv_bal_report.xml',
        'reports/print_template.xml',
        'views/wizard_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 50.00
}
