from odoo import api, fields, models, _
from odoo.addons.stock_account.models.stock_move import StockMove
from odoo.addons.purchase_stock.models.stock import StockMove as StockMovePurchase


def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
    self.ensure_one()

    move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
    if 'force_period_date' in self._context:
        date = self._context.get('force_period_date')
    elif self.picking_id and self.picking_id.date_done:
        date = self.picking_id.date_done
    else:
        date = fields.Date.context_today(self)
    return {
        'journal_id': journal_id,
        'line_ids': move_lines,
        'date': date,
        'ref': description,
        'stock_move_id': self.id,
        'stock_valuation_layer_ids': [(6, None, [svl_id])],
        'move_type': 'entry',
    }


StockMove._prepare_account_move_vals = _prepare_account_move_vals


def _get_price_unit(self):
    """ Returns the unit price for the move"""
    self.ensure_one()
    if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
        line = self.purchase_line_id
        order = line.order_id
        price_unit = line.price_unit
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=1.0)['total_void']
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            convert_date = fields.Date.context_today(self) if not self.date else self.date
            price_unit = order.currency_id._convert(price_unit, order.company_id.currency_id, order.company_id, convert_date, round=False)
        return price_unit
    return super(StockMovePurchase, self)._get_price_unit()


StockMovePurchase._get_price_unit = _get_price_unit
