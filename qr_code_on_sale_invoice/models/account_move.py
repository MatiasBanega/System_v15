from odoo import models, fields, api


class AccountInvoiceQRCode(models.Model):
    _inherit = 'account.move'

    def create_data_qr_code(self):
        """Create a data for qr_code for render in xml.
        Example:
            <img t-att-src="'/report/barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s' % ('QR', o.create_data_qr_code(), 100, 100)"/>
        """

        template = '{ruc}|{document_type_name}|{series}|{correlative}|{total_igv}|{total_amount}|' \
                   '{date_invoice}|{document_type_name_user}|{document_number_user}|\r\n'

        date_invoice = self.invoice_date.strftime('%d-%m-%Y') if self.invoice_date else ''
        series = self.name.replace(' ', '').split('-')[0] or '0000' if '-' in self.name else ''
        correlative = self.name.replace(' ', '').split('-')[1] or '' if '-' in self.name else ''

        data = template.format(
            ruc=self.company_id.vat or '',
            document_type_name=self.company_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or '',
            series=series,
            correlative=correlative,
            total_igv=self.amount_tax or 0.0,
            total_amount=self.amount_total or 0.0,
            date_invoice=date_invoice,
            document_type_name_user=self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or '',
            document_number_user=self.commercial_partner_id.vat or '00000000',
        )
        return data
