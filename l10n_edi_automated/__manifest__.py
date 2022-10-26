{
    'name': 'Send electronic invoices automatically',
    'version': '15.0.0.1.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'demo': 'https://www.ganemo.co/demo',
    'summary': 'Send electronic invoices immediately when the entry has been published',
    'description': '''
    This is a new module of the “odoo_edi” repo, which aims to automate the sending of the .xml to the validating entity. 
    In each Sales Diary, we will add a new boolean, with label: “Automatic delivery”, which will only be activated if a) The boolean “Use Documents?” is True. If this field is active in the journal, that after the Invoice is Posted, Odoo immediately executes the “Send Now” action of the invoice.
    It is applicable to the localization of electronic invoicing of several Countries that depend on the account_edi module.    
    ''',
    'category': 'Accounting',
    'depends': ['account_edi',
                'l10n_latam_invoice_document',
                ],
    'data': [
        'views/account_journal.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 148.00
}
