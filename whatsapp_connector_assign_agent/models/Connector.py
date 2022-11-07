
from odoo import models, fields


class Connector(models.Model):

    _inherit = 'acrux.chat.connector'

    assing_type = fields.Selection([('connector', 'Agents in connector'),
                                    ('crm_team', 'Crm Team')], string='Agent Assignment Type',
                                   default='connector', required=True)
    automatic_agent_assign = fields.Boolean('Automatic agents assign', default=False)
    assign_offline_agent = fields.Boolean('Assign inactive agents', default=False)
    agent_ids = fields.Many2many('res.users', 'connector_assign_agents', string='Agents to assign',
                                 domain="[('company_id', 'in', [company_id, False]), ('is_chatroom_group', '=', True)]")
    assing_agent_index = fields.Integer('Index to assign agents', default=0)
    retain_agent = fields.Boolean('Retain last Agent')
    assign_commercial = fields.Boolean('Always assign Commercial (Partner)',
                                       help='It has priority over other options.')
