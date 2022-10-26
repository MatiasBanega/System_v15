from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_pe_edi_get_edi_values(self, invoice):
        old_values = super(AccountEdiFormat, self)._l10n_pe_edi_get_edi_values(invoice)
        special_lines = invoice.invoice_line_ids.filtered(
            lambda l: not l.display_type == 'line_section' and l.price_subtotal < 0 and (l.product_id.l10n_pe_advance or l.product_id.global_discount))
        if special_lines:
            tmp_move = invoice._l10n_pe_edi_create_tmp_move_without_advance_lines()
            values = self._l10n_pe_edi_get_edi_values(tmp_move)
            sign = old_values['balance_multiplicator']

            # Subtract taxes from special lines in total taxes
            for special in special_lines:
                for tax_line in old_values['tax_details']['invoice_line_tax_details'][special]['tax_details']:
                    old_line_tax_data = old_values['tax_details']['invoice_line_tax_details'][special]['tax_details'][tax_line]
                    old_line_tax = old_line_tax_data['tax']
                    l10n_pe_edi_code = old_line_tax.tax_group_id.l10n_pe_edi_code
                    l10n_pe_edi_tax_code = old_line_tax.l10n_pe_edi_tax_code

                    old_total_tax = old_values['tax_details_grouped']['tax_details'].values()
                    tax = list(filter(lambda x: x['l10n_pe_edi_code'] == l10n_pe_edi_code and x['l10n_pe_edi_tax_code'] == l10n_pe_edi_tax_code, old_total_tax))

                    for tax_total in values['tax_details_grouped']['tax_details'].values():
                        if tax_total.get('l10n_pe_edi_code') == l10n_pe_edi_code and tax_total.get('l10n_pe_edi_tax_code') == l10n_pe_edi_tax_code:
                            if tax[0]['base_amount_currency'] < 0 and 0 > sign:
                                tax_total['base_amount_currency'] = tax[0]['base_amount_currency']
                            else:
                                tax_total['base_amount_currency'] = tax[0]['base_amount_currency'] * sign
                            if tax[0]['tax_amount_currency'] < 0 and 0 > sign:
                                tax_total['tax_amount_currency'] = tax[0]['tax_amount_currency']
                            else:
                                tax_total['tax_amount_currency'] = tax[0]['tax_amount_currency'] * sign
            total_tax_amount = old_values['total_tax_amount']
            invoice_date_due_vals_list, total_after_spot = self._l10n_pe_edi_get_spot_data(invoice)
            global_lines = special_lines.filtered(lambda x: not x.product_id.l10n_pe_advance and x.product_id.global_discount)
            if global_lines:
                values['line_extension_amount'] = old_values['line_extension_amount']
                values['tax_inclusive_amount'] = old_values['tax_inclusive_amount']
                values['payable_amount'] = old_values['payable_amount']
            values.update({
                'total_after_spot': total_after_spot,
                'order_reference': self._l10n_pe_edi_get_order_reference(invoice),
                'detraction_value': self._l10n_pe_edi_get_detraction_value(invoice),
                'document_description': invoice._l10n_pe_edi_amount_to_text(),
                'invoice_date_due_vals_list': invoice_date_due_vals_list,
                'l10n_pe_edi_delete_move_id': tmp_move,
                'record': invoice,
                'PaymentMeansID': old_values['PaymentMeansID'],
                'is_refund': old_values['is_refund'],
                'certificate_date': old_values['certificate_date'],
                'total_tax_amount': total_tax_amount
            })
            self._l10n_pe_edi_set_special_lines_vals(values, invoice, special_lines)
        else:
            values = old_values
        return values

    @staticmethod
    def _l10n_pe_edi_set_special_lines_vals(values, move_id, special_lines):
        """
        Filter and separate special lines (Example: Global discount and advance lines)
        """
        advance_lines_vals = []
        discount_lines_vals = []
        i = 1
        total_advance = 0.00
        total_discount = 0.00

        discount_percent_global = move_id.discount_percent_global / 100
        for line in special_lines:
            # Advance line
            if line.product_id.l10n_pe_advance:
                if not line.l10n_pe_advance_invoice:
                    raise ValidationError(f'{line.product_id.name}: Nombre de Anticipo vácio.')
                document_type_id_code = ''
                if move_id.l10n_latam_document_type_id.code == '01':
                    document_type_id_code = '02'
                elif move_id.l10n_latam_document_type_id.code == '03':
                    document_type_id_code = '03'
                else:
                    document_type_id_code = move_id.l10n_latam_document_type_id.code
                advance_line = {
                    'index': i,
                    'line': line,
                    'advance_name': line.l10n_pe_advance_invoice,
                    'partner_vat': move_id.partner_id.vat,
                    'company_vat': move_id.company_id.vat,
                    'partner_type_document': '6' if move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code != '6' else move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
                    'l10n_latam_document_type_id': document_type_id_code,
                    'datetime_document': move_id.invoice_date,
                    'tax_inclusive_amount': abs(line.price_total)
                }
                total_advance += advance_line['tax_inclusive_amount']
                advance_lines_vals.append(advance_line)
                i += 1

            # Discount global line
            if line.product_id.global_discount:
                product_id = line.product_id
                reason_code = product_id.l10n_pe_charge_discount_id and product_id.l10n_pe_charge_discount_id.code or '00'
                discount_global_line = {
                    'line': line,
                    'discount_charge_indicator': 'false' if reason_code not in ['45', '46', '47'] else 'true',
                    'discount_allowance_charge_reason_code': reason_code,
                    'discount_percent': discount_percent_global,
                    'discount_amount': abs(line.price_subtotal),
                    'base_amount': abs(line.price_subtotal / discount_percent_global),
                }
                if reason_code == '03':
                    total_discount += abs(line.price_subtotal)
                discount_lines_vals.append(discount_global_line)

        if advance_lines_vals:
            values['advance_lines_vals'] = advance_lines_vals
            values['total_advance'] = total_advance
            values['payable_amount'] -= total_advance

        if discount_lines_vals:
            values['discount_lines_vals'] = discount_lines_vals
            values['total_discount'] = total_discount
