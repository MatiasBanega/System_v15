from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    automated_sent = fields.Boolean(string='Envío Automático',
                                    help='''Si marca este campo, cuando una factura se publique se ejecutará de forma 
                                         inmediata la acción de Envío de la factura electrónica. Si no marca este 
                                         campo, el envío se ejecutará con el Cron de envío de facturas, 
                                         o al dar click en el botón "Enviar ahora".''')


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        super().action_post()
        if self.journal_id.automated_sent:
            docs = self.edi_document_ids.filtered(lambda d: d.state in ('to_send', 'to_cancel') and d.blocking_level != 'error' and d.move_id.move_type == 'out_invoice')
            docs._process_documents_web_services(with_commit=False)


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):

        action = super().reverse_moves()

        account_move = self.env['account.move'].browse(action['res_id'])
        if account_move.journal_id.automated_sent:
            account_move.edi_document_ids._process_documents_web_services(with_commit=False)

        return action