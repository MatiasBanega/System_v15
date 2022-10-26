import ast
import base64

from odoo.exceptions import ValidationError

from odoo import api, fields, models
from ..reports.sale_report_excel import SaleReportExcel, SaleReportTxt


class PleReportSale(models.Model):
    _name = 'ple.report.sale'
    _description = 'Reporte PLE Registro de Ventas'
    _inherit = 'ple.report.base'

    move_ids = fields.Many2many(
        comodel_name='account.move',
        string='Factura relacionadas'
    )

    @api.model
    def update_queries_functions(self):
        query_functions = """
    
                     CREATE or REPLACE FUNCTION validate_spaces(value VARCHAR)
                    -- Allows you to format a string without special characters and limit maximum characters
                    RETURNS VARCHAR
                    language plpgsql
                    as
                    $$
                    DECLARE
                       new_value VARCHAR;
                    BEGIN
                        IF value is NULL THEN
                            new_value =  '';
                        ELSE
                            new_value = value;
                            IF POSITION(' ' IN value) != 0 THEN
                                new_value = REPLACE(new_value, ' ', '');
                            END IF;
                        END IF;
                        RETURN new_value;
                    END;
                    $$;
                     
                     CREATE or REPLACE FUNCTION validate_string(value VARCHAR, max_len INTEGER)
                    -- Allows you to format a string without special characters and limit maximum characters
                    RETURNS VARCHAR
                    language plpgsql
                    as
                    $$
                    DECLARE
                       new_value VARCHAR;
                    BEGIN
                        IF value is NULL THEN
                            new_value =  '';
                        ELSE
                            new_value = value;
                            IF POSITION('-' IN value) != 0 THEN
                                new_value = REPLACE(new_value, '-', '');
                            END IF;
                            IF POSITION('/' IN value) != 0 THEN
                                new_value = REPLACE(new_value, '/', '');
                            END IF;
                            IF POSITION('\\n' IN value) != 0 THEN
                                new_value = REPLACE(new_value, '\\n', '');
                            END IF;
                            IF POSITION('&' IN value) != 0 THEN
                                new_value = REPLACE(new_value, '&', '');
                            END IF;
                            IF POSITION('á' IN value) != 0 THEN
                                new_value = REPLACE(new_value, 'á', 'a');
                            END IF;
                            IF POSITION('é' IN value) != 0 THEN
                                new_value = REPLACE(new_value, 'é', 'e');
                            END IF;
                            IF POSITION('í' IN value) != 0 THEN
                                new_value = REPLACE(new_value, 'í', 'i');
                            END IF;
                            IF POSITION('ó' IN value) != 0 THEN
                                new_value = REPLACE(new_value, 'ó', 'o');
                            END IF;
                            IF POSITION('ú' IN value) != 0 THEN
                                new_value = REPLACE(new_value, 'ú', 'u');
                            END IF;
                            IF POSITION('ñ' IN value) != 0 THEN
                                new_value = REPLACE(new_value, 'ñ', 'n-');
                            END IF;
                        END IF;
                        IF max_len IS NOT NULL AND max_len != -1 THEN
                            new_value = LEFT(new_value, max_len);
                        END IF;
                        RETURN new_value;
                    END;
                    $$;
                    --
                    --

                    CREATE or REPLACE FUNCTION get_tax(account_move_id INTEGER, move_type VARCHAR, l10n_document_type_code VARCHAR)
                    -- Allows you to calc amount by tax in all lines 
                    RETURNS RECORD
                    language plpgsql
                    as
                    $$
                    DECLARE
                        S_BASE_EXP NUMERIC := 0.0;
                        S_BASE_OG NUMERIC := 0.0;
                        S_BASE_OGD NUMERIC := 0.0;
                        S_TAX_OG NUMERIC := 0.0;
                        S_TAX_OGD NUMERIC := 0.0;
                        S_BASE_OE NUMERIC := 0.0;
                        S_BASE_OU NUMERIC := 0.0;
                        S_TAX_ISC NUMERIC := 0.0;
                        S_TAX_ICBP NUMERIC := 0.0;
                        S_BASE_IVAP NUMERIC := 0.0;
                        S_TAX_IVAP NUMERIC := 0.0;
                        S_TAX_OTHER NUMERIC := 0.0;
                        AMOUNT_TOTAL NUMERIC := 0.0;

                        tax_name VARCHAR := '';
                        tax_amount NUMERIC;
                        aml_line RECORD;
                        tax_row_line RECORD;
                        values RECORD;
                    BEGIN
                        FOR aml_line IN (SELECT * FROM account_move_line WHERE move_id = account_move_id AND parent_state != 'cancel') LOOP
                            FOR tax_row_line IN (SELECT * FROM account_account_tag WHERE 
                                id IN (SELECT account_account_tag_id FROM account_account_tag_account_move_line_rel WHERE account_move_line_id = aml_line.id)
                            ) LOOP
                                tax_amount = 0.0;
                                IF move_type = 'out_refund' AND tax_name IN ('S_BASE_OG', 'S_TAX_OG') AND l10n_document_type_code = '07' THEN
                                    tax_amount = ABS(aml_line.balance) * -1;
                                ELSE
                                    tax_amount = aml_line.balance * -1;
                                END IF;

                                tax_name = REPLACE(REPLACE(tax_row_line.name, '-', ''), '+', '');
                                IF tax_name = 'S_BASE_EXP' THEN
                                    S_BASE_EXP := S_BASE_EXP + tax_amount;
                                ELSIF tax_name = 'S_BASE_OG' THEN
                                    S_BASE_OG := S_BASE_OG + tax_amount;
                                ELSIF tax_name = 'S_BASE_OGD' THEN
                                    S_BASE_OGD := S_BASE_OGD + tax_amount;
                                ELSIF tax_name = 'S_TAX_OG' THEN
                                    S_TAX_OG := S_TAX_OG + tax_amount;
                                ELSIF tax_name = 'S_TAX_OGD' THEN
                                    S_TAX_OGD := S_TAX_OGD + tax_amount;
                                ELSIF tax_name = 'S_BASE_OE' THEN
                                    S_BASE_OE := S_BASE_OE + tax_amount;
                                ELSIF tax_name = 'S_BASE_OU' THEN
                                    S_BASE_OU := S_BASE_OU + tax_amount;
                                ELSIF tax_name = 'S_TAX_ISC' THEN
                                    S_TAX_ISC := S_TAX_ISC + tax_amount;
                                ELSIF tax_name = 'S_TAX_ICBP' THEN
                                    S_TAX_ICBP := S_TAX_ICBP + tax_amount;
                                ELSIF tax_name = 'S_BASE_IVAP' THEN
                                    S_BASE_IVAP := S_BASE_IVAP + tax_amount;
                                ELSIF tax_name = 'S_TAX_IVAP' THEN
                                    S_TAX_IVAP := S_TAX_IVAP + tax_amount;
                                ELSIF tax_name = 'S_TAX_OTHER' THEN
                                    S_TAX_OTHER := S_TAX_OTHER + tax_amount;
                                ELSE
                                    tax_amount = 0.0;  
                                END IF;
                                AMOUNT_TOTAL := AMOUNT_TOTAL + tax_amount;
                            END LOOP;
                        END LOOP;
                        values := (ROUND(S_BASE_EXP, 2), ROUND(S_BASE_OG, 2), ROUND(S_BASE_OGD, 2), ROUND(S_TAX_OG, 2), ROUND(S_TAX_OGD, 2), 
                                   ROUND(S_BASE_OE,2), ROUND(S_BASE_OU, 2), ROUND(S_TAX_ISC, 2), ROUND(S_TAX_ICBP, 2), ROUND(S_BASE_IVAP, 2), 
                                   ROUND(S_TAX_IVAP, 2), ROUND(S_TAX_OTHER, 2), ROUND(AMOUNT_TOTAL, 2));
                        RETURN values;
                    END;
                    $$;
    """
        self.env.cr.execute(query_functions)

    def action_generate_excel(self):
        query = """
                    SELECT
                    TO_CHAR(am.date, 'YYYYMM00') AS period,
                    replace(replace(replace(am.name, '/', ''), '-', ''), ' ', '') AS number_origin,
                    (SELECT
                        CASE
                            WHEN company.ple_type_contributor = 'CUO' THEN
                                (SELECT COALESCE(ple_correlative, 'M000000001') FROM account_move_line where move_id = am.id LIMIT 1)
                            WHEN company.ple_type_contributor = 'RER' THEN 'M-RER'
                            ELSE ''
                        END
                    ) AS journal_correlative,
                    TO_CHAR(am.invoice_date, 'DD/MM/YYYY') AS date_invoice,
                    CASE WHEN document_type.code is not null AND document_type.code = '14' AND am.state != 'cancel' THEN
                        TO_CHAR(am.invoice_date_due, 'DD/MM/YYYY') ELSE ''
                    END AS date_due,
                    COALESCE(document_type.code, '') AS voucher_sunat_code,
                    validate_spaces(validate_string(COALESCE(am.sequence_prefix, '0000'), -1)) AS voucher_series,
                    split_part(replace(am.name, ' ', ''), '-', 2) AS correlative,
                    COALESCE(identification_type.l10n_pe_vat_code, '') AS customer_document_type,
                    COALESCE(partner.vat, '') AS customer_document_number,
                    validate_string(partner.name, 99) AS customer_name,
                    get_tax(am.id, am.move_type, COALESCE(document_type.code, '')) AS tax_data,
                    currency.name AS code_currency,
                    ROUND(am.exchange_rate, 3) AS currency_rate,
                    COALESCE(TO_CHAR(am.origin_invoice_date, 'DD/MM/YYYY'), '') AS origin_date_invoice,
                    COALESCE(origin_document_type.code, '') AS origin_document_code,
                    split_part(replace(COALESCE(am.origin_number, ''), ' ', ''), '-', 1) AS origin_serie,
                    split_part(replace(COALESCE(am.origin_number, ''), ' ', ''), '-', 2) AS origin_correlative,
                    COALESCE(am.ple_state, '') AS ple_state,
                    am.id AS invoice_id,
                    {ple_report_sale_id} AS ple_report_sale_id

                    -- QUERIES TO MATCH MULTI TABLES
                    FROM account_move am
                    --  TYPE JOIN |  TABLE                         | VARIABLE                    | MATCH
                    --  https://www.sqlshack.com/sql-multiple-joins-for-beginners-with-examples/   
                        INNER JOIN  "res_partner"                    partner                       ON  am.partner_id = partner.id
                        INNER JOIN  "res_company"                    company                       ON  am.company_id = company.id
                        INNER JOIN  "res_currency"                   currency                      ON  am.currency_id = currency.id
                        LEFT JOIN   "l10n_latam_document_type"       origin_document_type          ON am.origin_l10n_latam_document_type_id = origin_document_type.id
                        LEFT JOIN   "l10n_latam_document_type"       document_type                 ON am.l10n_latam_document_type_id = document_type.id
                        LEFT JOIN   "l10n_latam_identification_type" identification_type           ON partner.l10n_latam_identification_type_id = identification_type.id
                    WHERE

                    -- FILTER QUERIES
                    ((((((((am."company_id" = {company_id}) AND
                            (am."move_type" in ('{move_type1}','{move_type2}'))) AND
                            (am."ple_date" >= '{date_start}')) AND
                            (am."ple_date" <= '{date_end}')) AND
                            ((am."state" not in ('{state}')) OR am."state" IS NULL)) AND
                            (am."journal_id" in (SELECT "account_journal".id FROM "account_journal" WHERE
                                                            ("account_journal"."ple_no_include" IS NULL or "account_journal"."ple_no_include" = false ) AND
                                                            ("account_journal"."company_id" IS NULL  OR ("account_journal"."company_id" in ({company_id})))
                                                            ORDER BY  "account_journal"."id"  ))) AND
                            (am."journal_id" in (SELECT "account_journal".id FROM "account_journal" WHERE ("account_journal"."type" = '{journal_type}') AND
                                                            ("account_journal"."company_id" IS NULL  OR ("account_journal"."company_id" in ({company_id})))
                                                            ORDER BY  "account_journal"."id"  ))) AND
                            (am."ple_its_declared" IS NULL or am."ple_its_declared" = false )) AND
                            (am."company_id" IS NULL  OR (am."company_id" in ({company_id})))

                    -- ORDER DATA
                    ORDER BY  am."date" DESC,am."name" DESC,am."id" DESC
                """.format(
            company_id=self.company_id.id,
            move_type1='out_invoice',
            move_type2='out_refund',
            date_start=self.date_start,
            date_end=self.date_end,
            state='draft',
            journal_type='sale',
            ple_report_sale_id=self.id
        )
        try:
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchall()
            self.get_excel_data(result)
        except Exception as error:
            raise ValidationError(f'Error al ejecutar queries, comunciar al administrador: \n {error}')

    def get_excel_data(self, data_lines):
        list_data = []
        invoices = []
        for obj_line in data_lines:
            tax_data = ast.literal_eval(obj_line['tax_data'])
            obj_line.update({
                'amount_export': tax_data[0],
                'amount_untaxed': tax_data[1],
                'discount_tax_base': tax_data[2],
                'sale_no_gravadas_igv': tax_data[3],
                'discount_igv': tax_data[4],
                'amount_exonerated': tax_data[5],
                'amount_no_effect': tax_data[6],
                'isc': tax_data[7],
                'tax_icbp': tax_data[8],
                'rice_tax_base': tax_data[9],
                'rice_igv': tax_data[10],
                'another_taxes': tax_data[11],
                'amount_total': tax_data[12],
            })
            value = {
                'period': obj_line.get('period', ''),
                'number_origin': obj_line.get('number_origin', ''),
                'journal_correlative': obj_line.get('journal_correlative', ''),
                'date_invoice': obj_line.get('date_invoice', ''),
                'date_due': obj_line.get('date_due', ''),
                'voucher_sunat_code': obj_line.get('voucher_sunat_code', ''),
                'voucher_series': obj_line.get('voucher_series', ''),
                'correlative': obj_line.get('correlative', ''),
                'correlative_end': '',
                'customer_document_type': obj_line.get('customer_document_type', ''),
                'customer_document_number': obj_line.get('customer_document_number', ''),
                'customer_name': obj_line.get('customer_name', ''),
                'amount_export': obj_line.get('amount_export', ''),
                'amount_untaxed': obj_line.get('amount_untaxed', ''),
                'discount_tax_base': obj_line.get('discount_tax_base', ''),
                'sale_no_gravadas_igv': obj_line.get('sale_no_gravadas_igv', ''),
                'discount_igv': obj_line.get('discount_igv', ''),
                'amount_exonerated': obj_line.get('amount_exonerated', ''),
                'amount_no_effect': obj_line.get('amount_no_effect', ''),
                'isc': obj_line.get('isc', ''),
                'rice_tax_base': obj_line.get('rice_tax_base', ''),
                'tax_icbp': "{0:.2f}".format(obj_line.get('tax_icbp', '')),
                'rice_igv': obj_line.get('rice_igv', ''),
                'another_taxes': obj_line.get('another_taxes', ''),
                'amount_total': float(obj_line.get('amount_export', '')) + float(obj_line.get('amount_untaxed', '')) + float(
                    obj_line.get('discount_tax_base', '')) + float(obj_line.get('sale_no_gravadas_igv', '')) + float(obj_line.get('discount_igv', '')) + float(
                    obj_line.get('amount_exonerated', '')) + float(obj_line.get('amount_no_effect', '')) + float(obj_line.get('rice_tax_base', '')) + float(
                    obj_line.get('tax_icbp', '')) + float(obj_line.get('rice_igv', '')) + float(obj_line.get('another_taxes', '')),
                'code_currency': obj_line.get('code_currency', ''),
                'currency_rate': "{0:.3f}".format(obj_line.get('currency_rate', '')),
                'origin_date_invoice': obj_line.get('origin_date_invoice', ''),
                'origin_document_code': obj_line.get('origin_document_code', ''),
                'origin_serie': obj_line.get('origin_serie', ''),
                'origin_correlative': obj_line.get('origin_correlative', ''),
                'contract_name': obj_line.get('contract_name', ''),
                'inconsistency_type_change': obj_line.get('inconsistency_type_change', ''),
                'payment_voucher': obj_line.get('payment_voucher', ''),
                'ple_state': obj_line.get('ple_state', ''),
            }
            list_data.append(value)
            invoices.append(obj_line['invoice_id'])

        sale_report = SaleReportTxt(self, list_data)
        values_content = sale_report.get_content()

        sale_report_xls = SaleReportExcel(self, list_data)
        values_content_xls = sale_report_xls.get_content()
        self.write({
            'txt_binary': base64.b64encode(values_content.encode() or '\n'.encode()),
            'txt_filename': sale_report.get_filename(),
            'error_dialog': 'No hay contenido para presentar en el registro de ventas electrónicos de este periodo.' if not values_content else '',
            'xls_binary': base64.b64encode(values_content_xls),
            'xls_filename': sale_report_xls.get_filename(),
            'date_ple': fields.Date.today(),
            'state': 'load',
            'move_ids': invoices
        })

    def action_close(self):
        super(PleReportSale, self).action_close()
        self.move_ids.write({'ple_its_declared': True})

    def action_rollback(self):
        super(PleReportSale, self).action_rollback()
        self.move_ids.write({'ple_its_declared': False})
        self.write({
            'txt_binary': False,
            'txt_filename': False,
            'xls_binary': False,
            'xls_filename': False,
            'move_ids': False
        })
