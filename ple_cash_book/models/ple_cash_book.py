from odoo import api, fields, models
from ..reports.report_ple_bank import BankReport
from ..reports.report_ple_cash import CashReport
import ast
import base64

from odoo.exceptions import ValidationError


class PleCashBank(models.Model):
    _name = 'ple.report.cash.bank'
    _description = 'Libro Caja y Bancos'
    _inherit = 'ple.report.base'

    move_ids = fields.Many2many(
        comodel_name='account.move',
        string='Factura relacionadas'
    )

    xls_filename_cash = fields.Char(string='Filename Excel - Efectivo')
    xls_binary_cash = fields.Binary(string='Reporte Excel - Efectivo')
    txt_filename_cash = fields.Char(string='Filename TXT - Efectivo')
    txt_binary_cash = fields.Binary(string='Reporte TXT - Efectivo')

    xls_filename_bank = fields.Char(string='Filename Excel - Cuentas corrientes')
    xls_binary_bank = fields.Binary(string='Reporte Excel - Cuentas corrientes')
    txt_filename_bank = fields.Char(string='Filename TXT - Cuentas corrientes')
    txt_binary_bank = fields.Binary(string='Reporte TXT - Cuentas corrientes')

    @api.model
    def update_queries_functions(self):
        query_functions = """
        
                    CREATE or REPLACE FUNCTION UDF_numeric_char(value NUMERIC)
                    --
                    RETURNS VARCHAR
                    language plpgsql
                    as
                    $$
                    DECLARE
                        value_res VARCHAR := ''; 
                    BEGIN
                        value_res := trim(to_char(value, '9999999.99'));
                        IF split_part(value_res, '.', '1') = '' THEN
                            value_res := CONCAT('0',value_res);		
                        END IF;
                        RETURN value_res;
                    END;
                    $$;
                    --
                    --
                    CREATE or REPLACE FUNCTION get_data_structured(account_move_name VARCHAR, account_move_date DATE, account_journal_type VARCHAR,
                    partner_country_id INTEGER, company_country_id INTEGER)
                    -- 
                    RETURNS VARCHAR
                    language plpgsql
                    as
                    $$
                    DECLARE
                        name VARCHAR := '';
                        date VARCHAR := '';
                        value_structured VARCHAR := '';
                        is_nodomicilied BOOL;
                    BEGIN
                        value_structured := '';
                        
                        name := replace(replace(account_move_name,'/', ''),'-', '');
                        date := TO_CHAR(account_move_date, 'YYYYMM00');
                        
                        IF partner_country_id = company_country_id THEN
                            is_nodomicilied := false;
                        ELSIF partner_country_id is not NULL THEN
                            is_nodomicilied := false;
                        ELSE
                            is_nodomicilied := true;
                        END IF;
                        
                        if journal.type = 'sale' THEN
                            value_structured := '140100&';
                        ELSIF journal.type = 'purchase' THEN
                            value_structured := '080200&';
                        ELSE
                            value_structured := '080100&';
                        END IF;
                        
                        value_structured := concat(value_structured,'&',date,'&',name,'&',correlative);
                        
                        RETURN  value_structured;
                    END;
                    $$;
                    --
                    --
                    CREATE or REPLACE FUNCTION find_full_reconcile(full_reconcile_id INTEGER, entrada TEXT, salida VARCHAR)
                    RETURNS VARCHAR
                    language plpgsql
                    as
                    $$
                    DECLARE
                    BEGIN
                        IF full_reconcile_id is not NULL THEN
                            RETURN entrada;
                        ELSE 
                            RETURN salida;
                        END IF;
                    END;
                    $$;                     
                    --
                    --
                    CREATE or REPLACE FUNCTION get_unit_operation_code(account_move_id INTEGER)
                    -- Allows you to concatenate values of account_analytic_tag
                    RETURNS VARCHAR
                    language plpgsql
                    as
                    $$
                    DECLARE
                        unit_operation_code VARCHAR := '';
                        aml_line RECORD;
                        aat_line RECORD;
                    BEGIN
                        FOR aml_line IN (SELECT * FROM account_move_line WHERE move_id = account_move_id AND parent_state = 'posted') LOOP
                            FOR aat_line IN (SELECT * FROM account_analytic_tag WHERE
                                id in (SELECT account_analytic_tag_id FROM account_analytic_tag_account_move_line_rel
                                WHERE account_move_line_id = aml_line.id)
                            ) LOOP
                                unit_operation_code := concat(unit_operation_code,'&',aat_line.name);
                            END LOOP;
                        END LOOP;
                        RETURN unit_operation_code;
                    END;
                    $$;
        """
        self.env.cr.execute(query_functions)


    def action_generate_excel(self):
        query_cash = """
                    SELECT
                    coalesce(TO_CHAR(account_move_line.date, 'YYYYMM00'), '') as period,
                    replace(replace(replace(account_move_line__move_id.name, '/', ''), '-', ''), ' ', '') as cuo,
                    (SELECT
                        CASE
                            WHEN company.ple_type_contributor = 'CUO' THEN
                                (SELECT COALESCE(ple_correlative, 'M000000001') FROM account_move_line WHERE move_id = account_move_line__move_id.id  LIMIT 1)
                            WHEN company.ple_type_contributor = 'RER' THEN 'M-RER'
                            ELSE ''
                        END
                    ) as correlative,
                    coalesce(trim(replace(replace(replace(account_account.code, '/', ''), '-', ''), '.', '')), '') as account_code,
                    get_unit_operation_code(account_move_line__move_id.id) as unit_operation_code,
                    coalesce(account_analytic.code, '') as cost_center_code,
                    coalesce(currency.name, 'PEN') as currency_name,
                    (SELECT 
                        CASE
                            WHEN account_move_line.serie_correlative IS NOT NULL THEN
                                SUBSTRING(split_part(replace(account_move_line.serie_correlative, ' ', ''), '-',1),1,4)
                            ELSE '0000'
                        END
                    ) as serie,
                    (SELECT 
                        CASE
                            WHEN account_move_line.serie_correlative IS NOT NULL THEN
                                SUBSTRING(split_part(replace(account_move_line.serie_correlative, ' ', ''), '-', 2),1,8)
                            ELSE '00000000'
                        END
                    ) as document_number,
                    coalesce(document_type.code, '00') AS type_payment_document,
                    coalesce(TO_CHAR(account_move_line__move_id.date, 'DD/MM/YYYY'), '') as accounting_date,
                    coalesce(TO_CHAR(account_move_line__move_id.invoice_date_due, 'DD/MM/YYYY'), '') as date_due,
                    coalesce(TO_CHAR(account_move_line__move_id.date, 'DD/MM/YYYY'), '') as operation_date,
                    (CASE WHEN account_move_line__move_id.ref IS NOT NULL THEN
                        account_move_line__move_id.ref ELSE
                            SUBSTRING(account_move_line.name,1 ,200) END) as gloss,
                    coalesce(account_move_line.name, '') as referential_gloss,
                    UDF_numeric_char(account_move_line.debit) as debit, 
                    UDF_numeric_char(account_move_line.credit) as credit,
                    (SELECT
                        CASE
                            WHEN account_move_line.full_reconcile_id is not NULL THEN
                                (SELECT get_data_structured(account_move.name,account_move.date,account_journal.type,res_partner.country_id,part.country_id) 
                                FROM account_move
                                INNER JOIN res_partner ON account_move.partner_id = res_partner.id
                                INNER JOIN account_journal ON account_move.journal_id = account_journal.id 
                                INNER JOIN res_company ON account_move.company_id = res_company.id
                                INNER JOIN res_partner as part ON res_company.partner_id = part.id
                                WHERE account_move.id = account_move_line__move_id.id)
                            ELSE ''
                        END
                    ) as data_structured   
                    -- QUERIES TO MATCH MULTI TABLES
                    FROM "account_move" as "account_move_line__move_id","account_move_line"
                    --  https://www.sqlshack.com/sql-multiple-joins-for-beginners-with-examples/
                    --  TYPE JOIN |  TABLE                         | VARIABLE                    | MATCH
                        LEFT JOIN   "account_account"                account_account       ON  account_move_line.account_id = account_account.id
                        INNER JOIN  "res_currency"                   currency              ON  account_move_line.currency_id = currency.id
                        INNER JOIN	"res_company"					 company			   ON  account_move_line.company_id = company.id
                        LEFT JOIN   "account_analytic_account"       account_analytic      ON  account_move_line.analytic_account_id = account_analytic.id
                        LEFT JOIN   "l10n_latam_document_type"       document_type         ON  account_move_line.l10n_latam_document_type_id = document_type.id
                    WHERE
                    -- FILTER QUERIES
                    ("account_move_line"."move_id"="account_move_line__move_id"."id") AND
                            ((((("account_move_line"."account_id" in (SELECT "account_account".id
                            FROM "account_account" WHERE "account_account"."ple_selection" = '{ple_selection}'
                            AND ("account_account"."company_id" IS NULL OR
                            ("account_account"."company_id" in ({company_id})))
                            ORDER BY "account_account"."id"))  AND
                            ("account_move_line"."date" >= '{date_start}'))  AND
                            ("account_move_line"."date" <= '{date_end}'))  AND
                            ("account_move_line"."company_id" = {company_id}))  AND
                            ("account_move_line__move_id"."state" = '{state}')) AND
                            ("account_move_line"."company_id" IS NULL   OR  ("account_move_line"."company_id" in ({company_id})))

                    -- ORDER DATA
                    ORDER BY "account_move_line"."date" DESC,"account_move_line"."move_name" DESC,"account_move_line"."id"
                """.format(
            ple_selection='cash',
            company_id=self.company_id.id,
            date_start=self.date_start,
            date_end=self.date_end,
            state='posted',
            ple_report_cash_bank=self.id
        )

        query_bank = """
                    SELECT

                    coalesce(TO_CHAR(account_move_line.date, 'YYYYMM00'), '') as period,
                    replace(replace(replace(account_move_line__move_id.name, '/', ''), '-', ''), ' ', '') as cuo,
                    (SELECT
                        CASE
                            WHEN company.ple_type_contributor = 'CUO' THEN
                                (SELECT COALESCE(ple_correlative, 'M000000001') FROM account_move_line WHERE move_id = account_move_line__move_id.id  LIMIT 1)
                            WHEN company.ple_type_contributor = 'RER' THEN 'M-RER'
                            ELSE ''
                        END
                    ) as correlative,
                    coalesce(res_bank.sunat_bank_code, '') as bank_code,
                    coalesce(res_partner_bank.acc_number, '') as account_bank_code,
                    TO_CHAR(account_move_line.date, 'DD/MM/YYYY') as date,
                    coalesce(account_move_line.name, '-') as operation_description,
                    coalesce(payment_methods.code, '003') as payment_method,
                    coalesce(identification_type.l10n_pe_vat_code, '-') as partner_type_document,
                    coalesce(partner.vat, '-') as partner_document_number,
                    coalesce(account_move_line.name, 'VARIOS') as partner_name,
                    (SELECT
                        CASE
                            WHEN account_move_line__move_id.ref is not NULL THEN
                                validate_string(account_move_line__move_id.ref, 20)
                            WHEN account_move_line__move_id.name is not NULL THEN
                                validate_string(account_move_line__move_id.name, 20)
                            ELSE ''
                        END
                    ) as transaction_number,
                    --trim(LEADING ' ' TO_CHAR(account_move_line.debit, '9999999.99')) as debit, 
                    --TO_CHAR(account_move_line.debit, '0.99') as debit, 
                    UDF_numeric_char(account_move_line.debit) as debit,     
                    UDF_numeric_char(account_move_line.credit) as credit
                    -- QUERIES TO MATCH MULTI TABLES
                    FROM "account_move" as "account_move_line__move_id","account_move_line"
                    --  https://www.sqlshack.com/sql-multiple-joins-for-beginners-with-examples/
                    --  TYPE JOIN |  TABLE                         | VARIABLE                    | MATCH
                        LEFT JOIN  "res_partner"                    partner               ON  account_move_line.partner_id = partner.id
                        LEFT JOIN   "account_account"                account_account       ON  account_move_line.account_id = account_account.id
                        INNER JOIN  "res_currency"                   currency              ON  account_move_line.currency_id = currency.id
                        INNER JOIN	"res_company"					 company			   ON  account_move_line.company_id = company.id
                        LEFT JOIN   "account_analytic_account"       account_analytic      ON  account_move_line.analytic_account_id = account_analytic.id
                        LEFT JOIN   "account_bank_statement_line"    account_bankSL        ON  account_move_line.statement_line_id = account_bankSL.id
                        LEFT JOIN   "payment_methods_codes"          payment_methods       ON  account_bankSL.means_payment_id = payment_methods.id
                        LEFT JOIN   "res_partner_bank"               res_partner_bank      ON  account_account.bank_id = res_partner_bank.id
                        LEFT JOIN   "res_bank"                       res_bank              ON  res_partner_bank.bank_id = res_bank.id
                        LEFT JOIN   "l10n_latam_identification_type" identification_type   ON partner.l10n_latam_identification_type_id = identification_type.id
                    WHERE
                    -- FILTER QUERIES
                    ("account_move_line"."move_id"="account_move_line__move_id"."id") AND
                            ((((("account_move_line"."account_id" in (SELECT "account_account".id
                            FROM "account_account" WHERE "account_account"."ple_selection" = '{ple_selection}'
                            AND ("account_account"."company_id" IS NULL OR
                            ("account_account"."company_id" in ({company_id})))
                            ORDER BY "account_account"."id"))  AND
                            ("account_move_line"."date" >= '{date_start}'))  AND
                            ("account_move_line"."date" <= '{date_end}'))  AND
                            ("account_move_line"."company_id" = {company_id}))  AND
                            ("account_move_line__move_id"."state" = '{state}')) AND
                            ("account_move_line"."company_id" IS NULL   OR  ("account_move_line"."company_id" in ({company_id})))
                    -- ORDER DATA
                    ORDER BY "account_move_line"."date" DESC,"account_move_line"."move_name" DESC,"account_move_line"."id"
                """.format(
            ple_selection='bank',
            company_id=self.company_id.id,
            date_start=self.date_start,
            date_end=self.date_end,
            state='posted',
            ple_report_cash_bank=self.id
        )

        try:
            self.env.cr.execute(query_cash)
            data_cash = self.env.cr.dictfetchall()
            self.env.cr.execute(query_bank)
            data_bank = self.env.cr.dictfetchall()
            print(data_bank)
            self.get_excel_data(data_cash, data_bank)

        except Exception as error:
            raise ValidationError(f'Error al ejecutar queries, comunciar al administrador: \n {error}')

    def get_excel_data(self, data_cash, data_bank):
        list_data_cash = []
        list_data_bank = []

        for obj_line_cash in data_cash:
            cash_values = {
                'period': obj_line_cash.get('period', ''),
                'cuo': obj_line_cash.get('cuo', ''),
                'correlative': obj_line_cash.get('correlative', ''),
                'account_code': obj_line_cash.get('account_code', ''),
                'unit_operation_code': obj_line_cash.get('unit_operation_code', ''),
                'cost_center_code': obj_line_cash.get('cost_center_code', ''),
                'currency_name': obj_line_cash.get('currency_name', ''),
                'type_payment_document': obj_line_cash.get('type_payment_document', ''),
                'serie': obj_line_cash.get('serie', ''),
                'document_number': obj_line_cash.get('document_number', ''),
                'accounting_date': obj_line_cash.get('accounting_date', ''),
                'date_due': obj_line_cash.get('date_due', ''),
                'operation_date': obj_line_cash.get('operation_date', ''),
                'gloss': obj_line_cash.get('gloss', ''),
                'referential_gloss': obj_line_cash.get('referential_gloss', ''),
                'debit': obj_line_cash.get('debit', '0.00'),
                'credit': obj_line_cash.get('credit', '0.00'),
                'data_structured': obj_line_cash.get('data_structured',''),
                'state': 1
            }
            list_data_cash.append(cash_values)

        for obj_line_bank in data_bank:
            bank_values = {
                'period': obj_line_bank.get('period', ''),
                'cuo': obj_line_bank.get('cuo', ''),
                'correlative': obj_line_bank.get('correlative', ''),
                'bank_code': obj_line_bank.get('bank_code', ''),
                'account_bank_code': obj_line_bank.get('account_bank_code', ''),
                'date': obj_line_bank.get('date', ''),
                'payment_method': obj_line_bank.get('payment_method', ''),
                'operation_description': obj_line_bank.get('operation_description', ''),
                'partner_type_document': obj_line_bank.get('partner_type_document', '-'),
                'partner_document_number': obj_line_bank.get('partner_document_number', '-'),
                'partner_name': obj_line_bank.get('partner_name', ''),
                'transaction_number': obj_line_bank.get('transaction_number', ''),
                'debit': obj_line_bank.get('debit', '0.00'),
                'credit': obj_line_bank.get('credit', '0.00'),
                'state': 1
            }
            list_data_bank.append(bank_values)

        report_cash = CashReport(self, list_data_cash)
        cash_content = report_cash.get_content_txt()
        cash_content_xls = report_cash.get_content_excel()
        cash_filename_txt = report_cash.get_filename(file_type='txt')
        cash_filename_xlsx = report_cash.get_filename(file_type='xlsx')

        report_bank = BankReport(self, list_data_bank)
        bank_content = report_bank.get_content_txt()
        bank_content_xls = report_bank.get_content_excel()
        bank_filename_txt = report_bank.get_filename(file_type='txt')
        bank_filename_xlsx = report_bank.get_filename(file_type='xlsx')

        error_dialog = ''
        if not cash_content:
            error_dialog += '- No hay contenido en el registro "Detalle de los movimientos del efectivo" de este periodo.\n'
        if not bank_content:
            error_dialog += '- No hay contenido en el registro "Detalle de los movimientos de la cuenta corriente" de este periodo.'

        self.write({
            'txt_binary_cash': base64.b64encode(cash_content and cash_content.encode() or '\n'.encode()),
            'txt_filename_cash': cash_filename_txt,
            'xls_binary_cash': base64.b64encode(cash_content_xls),
            'xls_filename_cash': cash_filename_xlsx,
            'txt_binary_bank': base64.b64encode(bank_content and bank_content.encode() or '\n'.encode()),
            'txt_filename_bank': bank_filename_txt,
            'xls_binary_bank': base64.b64encode(bank_content_xls),
            'xls_filename_bank': bank_filename_xlsx,
            'error_dialog': error_dialog,
            'date_ple': fields.Date.today(),
            'state': 'load',
        })

    def action_close(self):
        super(PleCashBank, self).action_close()

    def action_rollback(self):
        super(PleCashBank, self).action_rollback()
        self.write({
            'txt_binary_cash': False,
            'txt_filename_cash': False,
            'xls_binary_cash': False,
            'xls_filename_cash': False,
            'txt_binary_bank': False,
            'txt_filename_bank': False,
            'xls_binary_bank': False,
            'xls_filename_bank': False,
        })
