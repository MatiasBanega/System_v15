from odoo import api, fields, models
import pytz


class Account(models.Model):
    _inherit = 'account.account'

    ple_date_account = fields.Date(
        string='Fecha de cuenta',
        default=fields.Date.today
    )
    ple_state_account = fields.Selection(selection=[
        ('1', '1'),
        ('8', '8'),
        ('9', '9'),
    ], string='Estado', default='1')
    ple_selection = fields.Selection(
        selection=[],
        string="PLE"
    )


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    ple_journal_correlative = fields.Selection(
        selection=[
            ('A', 'Apertura'),
            ('C', 'Cierre'),
            ('M', 'Movimiento')
        ],
        default='M',
        string='Estado PLE'
    )
    ple_no_include = fields.Boolean(
        string='No includir en Registro del PLE',
        default=False,
        help="""
Si este campo está marcado, las facturas (documentos de compra y venta), que tengan este diario seteado, no aparecerán en el registro de compras o ventas del PLE. Sin perjuicio de que los asientos contables que dichas facturas generen, aparecerán en los libros que se elaboren con base a los asientos contables, como son el Libro Diario y Mayor.
"""
    )


class AccountMove(models.Model):
    _inherit = 'account.move'

    ple_state = fields.Selection(
        selection=[
            ('0', '0'),
            ('1', '1'),
            ('2', '2'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
        ],
        string='Estado PLE'
    )
    ple_its_declared = fields.Boolean(string='Declarado?')
    ple_date = fields.Date(
        string='Fecha PLE',
        help='Esta fecha sirve para decidir en qué periodo del PLE se presentará esta factura en el registro de compras'
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            tags = [('group', 'ple_group')]
            res = self.env['res.partner'].tags_invisible_per_country(tags, res, [self.env.ref('base.pe')])
        return res

    def update_ple_state(self):
        recs = self.filtered(lambda x: x.move_type in ['out_invoice', 'out_refund'])
        recs.update({'ple_state': '1'})

    @api.onchange('date')
    def onchange_ple_date_from_date(self):
        self.ple_date = self.date

    @api.onchange('invoice_date')
    def onchange_ple_date_from_invoice_date(self):
        self.ple_date = self.invoice_date

    @api.model
    def _convert_date_timezone(self, date_order, format_time='%Y-%m-%d %H:%M:%S'):
        user_tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
        date_tz = pytz.utc.localize(date_order).astimezone(user_tz)
        date_order = date_tz.strftime(format_time)
        return date_order

    @api.model_create_multi
    def create(self, values):
        for vals in values:
            if vals.get('date') and not vals.get('ple_date'):
                vals['ple_date'] = vals['date']
            if not vals.get('date') and not vals.get('ple_date'):
                vals['ple_date'] = fields.Date.context_today(self)
        obj = super(AccountMove, self).create(values)
        obj.update_ple_state()
        obj.update_lines_correlative()
        return obj

    def write(self, values):
        for rec in self:
            rec.update_cancel_ple_state(values)
            prefix = rec.get_ple_type_contributor()
            i = 1
            for line in rec.line_ids:
                line.update_correlative_cr(prefix, i)
                i += 1
            rec.change_ple_state_version(values)
        return super(AccountMove, self).write(values)

    def update_lines_correlative(self):
        for obj in self:
            prefix = obj.get_ple_type_contributor()
            obj.line_ids.update_correlative(prefix)

    def update_cancel_ple_state(self, values):
        self.ensure_one()
        document_type_id = self.l10n_latam_document_type_id and self.l10n_latam_document_type_id.code in ['01', '03']
        if self.move_type in ['out_invoice', 'out_refund'] and document_type_id and values.get('state') and values['state'] == 'cancel':
            values['ple_state'] = '2'
        return values

    def get_ple_type_contributor(self):
        self.ensure_one()
        new_name = self.journal_id.ple_journal_correlative or ''
        return new_name

    def change_ple_state_version(self, values):
        if 'ple_date' in values:
            ple_month = values['ple_date'].split('-')
            for recs in self:
                if recs.invoice_date and recs.date:
                    if recs.invoice_date.month < int(ple_month[1]) or recs.invoice_date.year < int(ple_month[0]):
                        values['ple_state'] = '8'
                    else:
                        values['ple_state'] = '1'
        self.update_cancel_ple_state(values)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    ple_correlative = fields.Char(string='Correlativo')

    def update_correlative(self, move_prefix):
        i = 1
        for line in self:
            if line.ple_correlative and line.ple_correlative != move_prefix:
                line.ple_correlative = '{}{}'.format(move_prefix, str(i).zfill(9))
            i += 1

    def update_correlative_cr(self, move_prefix, i):
        for line in self:
            if not line.ple_correlative:
                ple_correlative = '{}{}'.format(move_prefix, str(i).zfill(9))
                self._cr.execute("""UPDATE account_move_line
                                    SET ple_correlative=%s
                                    WHERE id=%s """,
                                 (ple_correlative, self.id))
