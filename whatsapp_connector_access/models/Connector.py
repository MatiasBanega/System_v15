# -*- coding: utf-8 -*-
from odoo import models, fields


class Connector(models.Model):
    _inherit = 'acrux.chat.connector'

    allowed_user_ids = fields.Many2many('res.users', 'chatroom_allowed_users', 'connector_id', 'user_id',
                                        string='User Access')
