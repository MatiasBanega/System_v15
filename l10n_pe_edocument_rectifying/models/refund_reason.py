from odoo import fields, models

refund_reason_13 = ('13', 'Corrección del monto neto pendiente de pago y/o la(s) de vencimiento del \n pago único o de las cuotas y/o los montos '
                          'correspondientes a cada cuota , de ser el caso')


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_pe_edi_refund_reason = fields.Selection(selection_add=[refund_reason_13])


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    l10n_pe_edi_refund_reason = fields.Selection(selection_add=[refund_reason_13])
