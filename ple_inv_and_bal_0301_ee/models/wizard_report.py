from datetime import date, datetime
from odoo import models, fields


class WizardReportGenerateTxt(models.TransientModel):
    _name = 'wizard.report.generate.0301.ee'
    _description = 'Financial report 3.1 EE - Wizard'

    report_model = fields.Char(string="Report Model", required=True)
    report_id = fields.Integer(string="Parent Report Id", required=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True
    )

    date_start = fields.Date(
        string='Fecha Inicio',
        required=True,
        default=datetime.today()
    )
    date_end = fields.Date(
        string='Fecha Fin',
        required=True,
        default=datetime.today()
    )

    state_send = fields.Selection(selection=[
        ('0', 'Cierre de Operaciones - Bajo de Inscripciones en el RUC'),
        ('1', 'Empresa o Entidad Operativa'),
        ('2', 'Cierre de libro - No Obligado a llevarlo')
    ], required=True,
        string='Estado de Envío',
        default='0'
    )

    date_ple = fields.Date(
        string='Generado el',
        required=True,
        default=datetime.today()
    )

    financial_statements_catalog = fields.Selection(
        selection=[
            ('01', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - SECTOR DIVERSAS - INDIVIDUAL'),
            ('02', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - SECTOR SEGUROS - INDIVIDUAL'),
            ('03', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - SECTOR BANCOS Y FINANCIERAS - INDIVIDUAL'),
            ('04', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - ADMINISTRADORAS DE FONDOS DE PENSIONES (AFP)'),
            ('05', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - AGENTES DE INTERMEDIACIÓN'),
            ('06', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - FONDOS DE INVERSIÓN'),
            ('07', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - PATRIMONIO EN FIDEICOMISOS'),
            ('08', 'SUPERINTENDENCIA DEL MERCADO DE VALORES - ICLV'),
            ('09', 'OTROS NO CONSIDERADOS EN LOS ANTERIORES')
        ],
        string='Catálogo estados financieros',
        default='09',
        required=True,
    )

    eeff_presentation_opportunity = fields.Selection(
        selection=[
            ('01', 'Al 31 de diciembre'),
            ('02', 'Al 31 de enero, por modificación del porcentaje'),
            ('03', 'Al 30 de junio, por modificación del coeficiente o porcentaje'),
            ('04',
             'Al último día del mes que sustentará la suspensión o modificación del coeficiente (distinto al 31 de enero o 30 de junio)'),
            ('05',
             'Al día anterior a la entrada en vigencia de la fusión, escisión y demás formas de reorganización de sociedades o emperesas o extinción '
             'de la persona jurídica'),
            ('06', 'A la fecha del balance de liquidación, cierre o cese definitivo del deudor tributario'),
            ('07', 'A la fecha de presentación para libre propósito')
        ],
        string='Oportunidad de presentación de EEFF',
        required=True,
        default='01'
    )

    txt_filename = fields.Char(string='Filaname .txt')
    txt_binary = fields.Binary(string='Reporte .TXT 3.1')
    m2o_ple_report_inv_bal_01 = fields.Many2one('ple.report.inv.bal.01')

    def action_generate_txt(self):
        self.ensure_one()

        self.m2o_ple_report_inv_bal_01 = self.env["ple.report.inv.bal.01"].create(
            {
                'company_id': self.company_id.id,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'state_send': self.state_send,
                'date_ple': self.date_ple,
                'financial_statements_catalog': self.financial_statements_catalog,
                'eeff_presentation_opportunity': self.eeff_presentation_opportunity,
            }
        )

        self.action_generate_initial_balances_301()
        self.m2o_ple_report_inv_bal_01.action_generate_excel()

        data = {
            'txt_binary': self.m2o_ple_report_inv_bal_01.txt_binary,
            'txt_filename': self.m2o_ple_report_inv_bal_01.txt_filename,
        }
        self.write(data)
        self.m2o_ple_report_inv_bal_01.unlink()

        return self.action_return_wizard()

    def action_return_wizard(self):
        wizard_form_id = self.env.ref('ple_inv_and_bal_0301_ee.wizard_report_generate_txt_view').id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.report.generate.txt',
            'views': [(wizard_form_id, 'form')],
            'view_id': wizard_form_id,
            'res_id': self.id,
            'target': 'new'
        }
