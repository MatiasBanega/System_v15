from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_pe_edi_provider = fields.Selection(selection_add=[('ose', 'OSE')])
    l10n_pe_edi_provider_ose_prod_wsdl = fields.Char(string="OSE WSDL")
    l10n_pe_edi_provider_ose_test_wsdl = fields.Char(string="OSE WSDL (Test)")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_pe_edi_provider_ose_prod_wsdl = fields.Char(
        string="OSE WSDL",
        related="company_id.l10n_pe_edi_provider_ose_prod_wsdl",
        readonly=False,
    )
    l10n_pe_edi_provider_ose_test_wsdl = fields.Char(
        string="OSE WSDL (Test)",
        related="company_id.l10n_pe_edi_provider_ose_test_wsdl",
        readonly=False,
    )
