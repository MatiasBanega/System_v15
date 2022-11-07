
from odoo import models, fields


class CrmTeam(models.Model):

    _inherit = 'crm.team'

    assing_agent_index = fields.Integer('Index to assign agents', default=0)
