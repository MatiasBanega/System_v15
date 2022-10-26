from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    ple_selection = fields.Selection(
        selection_add=[
            ("cash", "1.1 Libro Caja y Bancos: Efectivo"),
            ("bank", "1.2 Libro Caja y Bancos: Cuentas corrientes")]
    )
    bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string='Cuenta Bancaria'
    )
    user_account_type = fields.Selection(
        string='Tipo de cuenta',
        related='user_type_id.type'
    )

    @api.onchange('user_account_type')
    def onchange_bank_id(self):
        if self.user_account_type and self.user_account_type != 'liquidity' and self.bank_id:
            self.bank_id = False

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    means_payment_id = fields.Many2one(
        comodel_name='payment.methods.codes',
        string="Medio de pago - libro de bancos",
        default=lambda self: self._get_default_means_payment()
    )
    
    def _get_default_means_payment(self):
        means_payment_id = self.env['payment.methods.codes'].search([('code', '=', '003')])
        if means_payment_id:
            return means_payment_id.id