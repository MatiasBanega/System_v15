# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.osv import expression
from odoo.exceptions import UserError


class Conversation(models.Model):
    _inherit = 'acrux.chat.conversation'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        ctx = self.env.context
        if not (ctx.get('acrux_from_chatter') or ctx.get('acrux_from_message_wizard') or self.env.user._is_system()):
            domain = self.get_access_agent(args)
            if domain:
                args = expression.AND([domain, args]) if args else domain
        return super(Conversation, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                                                 access_rights_uid=access_rights_uid)

    @api.model
    def get_access_agent(self, args):
        return []

    def acrux_access_member_ids(self, datas, users, member_ids, access_group):
        result = []
        for data in datas:
            if data[1] == 'new_messages':
                if not users:
                    continue
                if 'private' in data[0]:
                    user_id = data[0][-1]
                    if user_id not in users.ids:
                        continue
                    if user_id not in member_ids:
                        user = users.filtered(lambda x: x.id == user_id)
                        if user.has_group(access_group):
                            continue
                    result.append(data)
                else:
                    notify_users = users.filtered(lambda x: x.id in member_ids or not x.has_group(access_group))
                    if len(notify_users) == len(users):
                        result.append(data)
                        continue
                    for user in notify_users:
                        result.append([self.get_channel_to_one(user_id=user), data[1], data[2]])
            else:
                result.append(data)
        return result

    def acrux_access_field_empty(self, datas, users, field_value, access_group, not_implied_group):
        if not field_value:
            return datas

        def has_group(u):
            return u.has_group(access_group) and not u.has_group(not_implied_group)

        result = []
        for data in datas:
            if data[1] == 'new_messages':
                if not users:
                    continue
                if 'private' in data[0]:
                    user_id = data[0][-1]
                    if user_id not in users.ids:
                        continue
                    user = users.filtered(lambda x: x.id == user_id)
                    if has_group(user):
                        continue
                    result.append(data)
                else:
                    notify_users = users.filtered(lambda x: not has_group(x))
                    if len(notify_users) == len(users):
                        result.append(data)
                        continue
                    for user in notify_users:
                        result.append([self.get_channel_to_one(user_id=user), data[1], data[2]])
            else:
                result.append(data)
        return result

    def delegate_conversation(self):
        ''' is ensure_one '''
        if self.tmp_agent_id:
            domain = [('number', '=', self.number), ('connector_id', '=', self.connector_id.id)]
            if not self.with_user(self.tmp_agent_id).search(domain, limit=1).ids:
                raise UserError(_('The user has no access to this conversation.'))
        return super(Conversation, self).delegate_conversation()
