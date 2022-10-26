from odoo import api, fields, models
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    multiplier_factor_field = fields.Char(string='Multiplier Label', compute='_compute_multiplier_factor_field', store=True)
    amount_field_advance = fields.Char(string='Amount Label', compute='_compute_multiplier_factor_field', store=True)
    debit_field_advance = fields.Char(string='Debit Label', compute='_compute_multiplier_factor_field', store=True)

    @api.depends('invoice_payment_term_id')
    def _compute_multiplier_factor_field(self):
        for rec in self:
            if rec.tax_totals_json:
                invoice_info = json.loads(rec.tax_totals_json)
            if rec.invoice_payment_term_id and rec.invoice_payment_term_id.line_ids:
                for payment in rec.invoice_payment_term_id.line_ids:
                    if payment.l10n_pe_is_detraction_retention:
                        rec.multiplier_factor_field = str(round(payment.value_amount / 100, 4))
            else:
                rec.multiplier_factor_field = False
            if rec.line_ids:
                for line in rec.line_ids:
                    if line.l10n_pe_is_detraction_retention:
                        rec.amount_field_advance = str(round(line.amount_currency, 2))
                        rec.debit_field_advance = str(round(float(invoice_info['amount_total']), 2))
            else:
                rec.amount_field_advance = False
                rec.debit_field_advance = False

    def _l10n_pe_edi_copy_data_without_advance_lines(self, default=None):
        """
        Function that obtains all the data of an account.move record and filters the negative lines
        """
        data = self.copy_data(default=default)
        new_line_ids = []
        for line in data[0]['line_ids']:
            if line[2]['price_subtotal'] >= 0:
                if line[2]['exclude_from_invoice_tab']:
                    continue
                line[2]['recompute_tax_line'] = True
                new_line_ids.append(line)
        data[0]['invoice_line_ids'] = new_line_ids
        del data[0]['line_ids']
        return data

    def _l10n_pe_edi_create_tmp_move_without_advance_lines(self):
        """
        Duplicate a move without advance lines
        """
        data = self._l10n_pe_edi_copy_data_without_advance_lines()
        tmp_move = self.create(data[0])
        tmp_move._onchange_recompute_dynamic_lines()
        return tmp_move


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_pe_advance_invoice = fields.Char(string='Factura Anticipo FXXX-X')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_pe_advance = fields.Boolean(string='Anticipo')

    @api.onchange('l10n_pe_advance')
    def checkbox_set_true_advance(self):
        for product in self:
            if product.l10n_pe_advance:
                product.global_discount = True

    @api.onchange('global_discount')
    def checkbox_set_true_discount(self):
        for product in self:
            if product.global_discount:
                product.l10n_pe_advance = True


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('l10n_pe_advance')
    def checkbox_set_true_advance(self):
        for product in self:
            if product.l10n_pe_advance:
                product.global_discount = True

    @api.onchange('global_discount')
    def checkbox_set_true_discount(self):
        for product in self:
            if product.global_discount:
                product.l10n_pe_advance = True


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    def _render(self, values=None, engine='ir.qweb', minimal_qcontext=False):
        """
        Delete temporal l10n_pe_edi account.move registry
        """
        template_render = super(IrUiView, self)._render(values, engine=engine, minimal_qcontext=minimal_qcontext)
        if values and values.get('l10n_pe_edi_delete_move_id'):
            values['l10n_pe_edi_delete_move_id'].unlink()
        return template_render
