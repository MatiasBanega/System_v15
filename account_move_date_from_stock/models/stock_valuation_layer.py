from datetime import datetime
from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    accounting_date = fields.Datetime(
        string='Fecha contable',
        default=datetime.now()
    )

    @api.model_create_multi
    def create(self, values):
        for v in values:
            if v.get("stock_move_id", False):
                move = self.env['stock.move'].browse(v['stock_move_id'])
                v['accounting_date'] = move.date if move else datetime.now()
        return super(StockValuationLayer, self).create(values)
