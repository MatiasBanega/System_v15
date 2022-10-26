{
    'name': 'Factura electrónica ilimitada para Perú',
    'version': '15.0.0.12.9',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'summary': 'Add validation services for electronic invoicing, which allows you to validate directly with SUNAT or with any authorized OSE provider.',
    'category': 'Accounting',
    'depends': [
        'l10n_pe_edi',
        'tributary_address_extension',
        'account_discount_global',
        'payment_term_lines',
        'l10n_pe_catalog'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/2.1/edi_base_templates.xml',
        'data/2.1/edi_invoice_templates.xml',
        'wizards/account_invoice_correction_view.xml',
        'views/account_views.xml',
        'views/res_config_settings_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 200.00
}
