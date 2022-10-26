from odoo import models, fields, api
from odoo.tools.translate import _


class AccountInvoiceCorrection(models.TransientModel):
    _name = 'account.invoice.correction'
    _description = 'Add Account Move Correction'

    move_id = fields.Many2one(
        string='Asiento contable',
        comodel_name='account.move',
        domain=[('edi_state', '=', 'sent'), ('l10n_pe_edi_refund_reason', '=', '13')]
    )
    journal_id = fields.Many2one(
        string='Diario específico',
        comodel_name='account.journal',
        domain=[('type', '=', 'sale'), ('l10n_latam_use_documents', '=', False)],
        help='Si está vacío, utiliza el diario del asiento contable para hacer el cargo.'
    )

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoiceCorrection, self).default_get(fields)
        move_id = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get(
            'active_model') == 'account.move' else self.env['account.move']
        if 'move_id' in fields:
            res['move_id'] = move_id.id
        return res

    def _prepare_account_move(self, move):
        return {
            'move_type': 'out_invoice',
            'partner_id': move.partner_id,
            'ref': move.name or False,
            'date': move.date,
            'invoice_payment_term_id': move.invoice_payment_term_id.id or False,
            'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
            'invoice_user_id': move.invoice_user_id.id,
            'currency_id': move.currency_id.id,
            'company_id': move.company_id.id,
        }

    def _prepare_account_move_line(self, move_line):
        return {
            'name': move_line.name,
            'product_id': move_line.product_id.id or False,
            'quantity': move_line.quantity,
            'product_uom_id': move_line.product_uom_id.id or False,
            'price_unit': abs(move_line.price_unit),
            'discount': move_line.discount or False,
            'analytic_tag_ids': [(6, 0, move_line.analytic_tag_ids.ids)],
            'account_id': move_line.account_id.id,
            'tax_ids': [(6, 0, move_line.tax_ids.ids)],
            'analytic_account_id': move_line.analytic_account_id.id or False,
            'company_id': move_line.company_id.id
        }

    def create_invoice_correction(self):
        self.ensure_one()
        move = self.move_id
        invoice_line_list = []
        move_to_redirect = self.env['account.move']

        for invoice_line in move.invoice_line_ids:
            move_line = self._prepare_account_move_line(invoice_line)
            invoice_line_list.append((0, 0, move_line))

        vals_move = self._prepare_account_move(move)
        vals_move['invoice_line_ids'] = invoice_line_list

        new_move = self.env['account.move'].create(vals_move)
        move_msg = _(
            "Esta factura de corrección fue creada a partir de:") + " <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>" % (
                   move.id, move.name)
        new_move.message_post(body=move_msg)
        move_to_redirect |= new_move

        action = {
            'name': _('Factura de corrección'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
        }
        action.update({
            'view_mode': 'form',
            'res_id': move_to_redirect.id,
        })
        return action
