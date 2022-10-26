from odoo import fields, models, api, _
import markupsafe
from markupsafe import Markup

from odoo.tools import config, date_utils, get_lang
import lxml.html


class ReportAccountFinancialReportInherit(models.Model):
    _inherit = "account.financial.html.report"

    allow_txt_generation = fields.Selection(selection_add=[('01', '3.1 Estado de situación financiera')])
    change_header_0301_ee = fields.Boolean(default=True)

    def _get_reports_buttons(self, options):
        res = super(ReportAccountFinancialReportInherit, self)._get_reports_buttons(options)

        if self.allow_txt_generation == '01':
            res += [{'name': _('Exportar a txt'), 'sequence': 3, 'action': 'open_report_export_txt_wizard_0301_ee'}]
        return res

    def open_report_export_txt_wizard_0301_ee(self, options):
        new_wizard = self.env['wizard.report.generate.0301.ee'].create(
            {'report_model': self._name, 'report_id': self.id})
        view_id = self.env.ref('ple_inv_and_bal_0301_ee.wizard_report_generate_0301_ee_txt_view').id
        new_context = self.env.context.copy()
        new_context['account_report_generation_options'] = options
        return {
            'type': 'ir.actions.act_window',
            'name': _('Export'),
            'view_mode': 'form',
            'res_model': 'wizard.report.generate.txt',
            'target': 'new',
            'res_id': new_wizard.id,
            'views': [[view_id, 'form']],
            'context': new_context,
        }

    def get_pdf(self, options):
        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.

        if self.allow_txt_generation != '01':
            return super(ReportAccountFinancialReportInherit, self).get_pdf(options)

        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env[
            'ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.company,
        }

        body_html = self.with_context(print_mode=True).get_html(options)
        body = self.env['ir.ui.view']._render_template(
            "account_reports.print_template",
            values=dict(rcontext, body_html=body_html),
        )
        body_string = str(body)

        if self.change_header_0301_ee:
            special_header = \
                self.env.ref("ple_inv_and_bal_0301_ee.action_print_report_pdf", False)._render_qweb_html(self.id)[0]
            x = self.env.ref("ple_inv_and_bal_0301_ee.action_print_report_pdf")
            body_string = body_string.replace('<body class="o_account_reports_body_print">',
                                              '<body class="o_account_reports_body_print">' + special_header.decode() + str(
                                                  body_html))
        else:
            body_string = body_string.replace('<body class="o_account_reports_body_print">',
                                              '<body class="o_account_reports_body_print">' + str(body_html))

        body = Markup(body_string)
        footer = self.env['ir.actions.report']._render_template("web.internal_layout", values=rcontext)
        footer = self.env['ir.actions.report']._render_template("web.minimal_layout", values=dict(rcontext, subst=True,
                                                                                                  body=Markup(
                                                                                                      footer.decode())))

        landscape = False
        if len(self.with_context(print_mode=True).get_header(options)[-1]) > 5:
            landscape = True

        return self.env['ir.actions.report']._run_wkhtmltopdf(
            [body],
            footer=footer.decode(),
            landscape=landscape,
            specific_paperformat_args={
                'data-report-margin-top': 10,
                'data-report-header-spacing': 10
            }
        )
