# -*- coding: utf-8 -*-
import random
import time
import logging
from odoo import models, api
from psycopg2 import OperationalError
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY
from odoo.addons.whatsapp_connector.tools import date_timedelta
_logger = logging.getLogger(__name__)


class Conversation(models.Model):

    _inherit = 'acrux.chat.conversation'

    def get_to_done(self):
        out = super(Conversation, self).get_to_done()
        if not out.get('agent_id'):
            out['agent_id'] = self.agent_id.id
        return out

    def get_to_new(self):
        out = super(Conversation, self).get_to_new()
        # assign_commercial
        commercial_id = self.res_partner_id.user_id
        if self.connector_id.assign_commercial and commercial_id and \
                (self.connector_id.assign_offline_agent or commercial_id.chatroom_active()):
            out['agent_id'] = commercial_id.id
        # retain_agent
        elif self.connector_id.retain_agent and self.agent_id and \
                (self.connector_id.assign_offline_agent or self.agent_id.chatroom_active()):
            out['agent_id'] = self.agent_id.id
        if not out.get('agent_id'):
            if self.connector_id.automatic_agent_assign or self.env.context.get('automatic_agent_assign'):
                out['agent_id'] = self.get_default_agent()
        return out

    def get_possible_agents(self):
        self.ensure_one()
        agent_ids = None
        main_model = None
        connector_id = self.connector_id
        if connector_id.assing_type == 'connector':
            agent_ids = connector_id.agent_ids
            main_model = connector_id
        elif connector_id.assing_type == 'crm_team':
            team_id = self.team_id or connector_id.team_id
            agent_ids = team_id.member_ids
            main_model = team_id
        return main_model, agent_ids

    def get_default_agent(self):
        self.ensure_one()
        agent_id = False
        connector_id = self.connector_id
        commercial_id = self.res_partner_id.user_id
        main_model, agent_ids = self.get_possible_agents()
        if commercial_id and commercial_id in agent_ids and \
                (connector_id.assign_offline_agent or commercial_id.chatroom_active()):
            agent_id = commercial_id
        ignore_users = self.env['res.users']
        if not agent_id:
            if self.agent_id:
                if (connector_id.assign_offline_agent or self.agent_id.chatroom_active()) \
                        and self.agent_id in agent_ids and not self.env.context.get('ignore_agent_id'):
                    agent_id = self.agent_id
                else:
                    ignore_users |= self.agent_id
        if not agent_id and main_model and agent_ids:
            agent_id = self.get_assign_chatroom_agent(main_model, agent_ids, ignore_users)
        return agent_id

    def get_assign_chatroom_agent(self, main_model, agent_ids, ignore_users):
        def is_valid(option, connector_id):
            return option.chatroom_active() or connector_id.assign_offline_agent

        self.ensure_one()
        concurrency_tries = 5
        connector_id = self.connector_id
        agent_id = False
        while concurrency_tries > 0:  # en caso de concurrencia se reintenta 5 veces
            try:
                agent_ids = agent_ids.sorted(lambda x: x.id)
                size = len(agent_ids)
                assing_agent_index = main_model.read(['assing_agent_index'])[0]['assing_agent_index']
                for _index in range(size):
                    assing_agent_index = (assing_agent_index % size) + 1
                    option = agent_ids[assing_agent_index - 1]
                    if option not in ignore_users:  # es una opcion
                        if is_valid(option, connector_id):
                            agent_id = option
                            main_model.write({'assing_agent_index': assing_agent_index})
                            break
                concurrency_tries = 0  # terminar el while
            except OperationalError as e:
                if e.pgcode in PG_CONCURRENCY_ERRORS_TO_RETRY:
                    concurrency_tries -= 1
                    time.sleep(random.uniform(0.0, 1.5))
                else:
                    raise e
        return agent_id

    @api.model
    def conversation_verify_reassign_agent_search(self, conn_id):
        if conn_id.time_to_reasign:
            date_to_news = date_timedelta(minutes=-conn_id.time_to_reasign)
            return self.search([('connector_id', '=', conn_id.id),
                                ('status', '=', 'new'),
                                ('last_received_first', '!=', False),
                                ('last_received_first', '<', date_to_news)])
        else:
            return self.env['acrux.chat.conversation']

    @api.model
    def conversation_verify_reassign_agent(self):
        ''' Call from cron or direct '''
        Connector = self.env['acrux.chat.connector'].sudo()
        to_news_ids = 0
        for conn_id in Connector.search([('automatic_agent_assign', '=', True)]):
            sctx = self.sudo().with_context(tz=conn_id.tz,
                                            lang=conn_id.company_id.partner_id.lang,
                                            allowed_company_ids=[conn_id.company_id.id])
            to_news = sctx.conversation_verify_reassign_agent_search(conn_id)
            if len(to_news):
                to_news_ids += len(to_news)
                for to_x in to_news:
                    to_x.event_create('unanswered', user_id=to_x.agent_id)
                    agent_id = to_x.with_context(ignore_agent_id=True).get_default_agent()
                    to_x.agent_id = agent_id.id
                    to_x.tmp_agent_id = False
                    to_x.delegate_conversation()
        _logger.info('________ | conversation assign_agent: %s' % to_news_ids)
