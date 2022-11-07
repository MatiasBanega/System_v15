# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.osv import expression


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if self.env.context.get('is_acrux_chat_room') and self.env.context.get('filter_connector_id'):
            args = args or []
            connector_id = self.env['acrux.chat.connector'].browse(self.env.context.get('filter_connector_id'))
            agent_ids = connector_id.agent_ids
            if agent_ids:
                if not connector_id.assign_offline_agent:
                    agent_ids = agent_ids.filtered('acrux_chat_active')
                domain = [('id', 'in', agent_ids.ids)]
                return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return super(ResUsers, self)._name_search(name=name, args=args, operator=operator, limit=limit,
                                                  name_get_uid=name_get_uid)
