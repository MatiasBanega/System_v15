import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import logging
_logger = logging.getLogger(__name__)


class WhatsappInstance(models.Model):
    _name = "whatsapp.instance"
    _description = 'Whatsapp Instance'

    def _get_default_sequence(self):
        return self.search([], order='sequence desc', limit=1).sequence + 1

    name = fields.Char('Name', required=True)
    status = fields.Selection([('enable', 'Enable'), ('disable', 'Disable')], string='Status', default='disable', copy=False)
    provider = fields.Selection([('whatsapp_chat_api', 'Whatsapp Chat Api'), ('gupshup', 'Gupshup')], string="Whatsapp Service Provider",
                                default='whatsapp_chat_api')
    whatsapp_endpoint = fields.Char('Whatsapp Endpoint', help="Whatsapp chat api endpoint url with instance id", copy=False)
    whatsapp_token = fields.Char('Whatsapp Token', help="Whatsapp chat api token", copy=False)
    send_whatsapp_through_template = fields.Boolean(string='Send Message Through Template', help='Send Message Through Template Using Respective Provider')
    whatsapp_gupshup_api_key = fields.Char('Gupshup Api Key', copy=False)
    whatsapp_gupshup_app_name = fields.Char('Gupshup App Name', copy=False)
    gupshup_source_number = fields.Char('Gupshup Phone Number', copy=False)
    signature = fields.Char(string='Signature')

    default_instance = fields.Boolean('Default Instance', required=True,
                                      help="Only one instance is default instance if whatsapp instance is not selected from users & "
                                           "message is sent from this instance")
    user_ids = fields.One2many('res.users', 'whatsapp_instance_id', string='Connected Users',
                               help="Message is send from this instance when these user is logged in")
    res_company_ids = fields.One2many('res.company', 'whatsapp_instance_id', string='Connected Companies')
    whatsapp_template_ids = fields.One2many('whatsapp.templates', 'whatsapp_instance_id', string='Whatsapp Templates')
    sequence = fields.Char(string="Sequence", readonly=True, required=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        # Allow provider wise only one default instance is true
        if 'default_instance' in vals and vals.get('provider'):
            if vals.get('default_instance'):
                for whatsapp_instance_id in self.env['whatsapp.instance'].sudo().search([('provider', '=', vals.get('provider'))]):
                    if whatsapp_instance_id.default_instance:
                        raise UserError(_('You already added default instance to another instance for %s provider') % whatsapp_instance_id.provider)
        return super(WhatsappInstance, self).create(vals)

    def write(self, vals):
        # Allow provider wise only one default instance is true
        if 'default_instance' in vals:
            for whatsapp_instance_id in self.env['whatsapp.instance'].sudo().search([('provider', '=', self.provider)]):
                if not vals['default_instance']:
                    vals['default_instance'] = False
                elif whatsapp_instance_id.default_instance:
                    raise UserError(_('You already added default instance to another instance for %s provider') % whatsapp_instance_id.provider)
        return super(WhatsappInstance, self).write(vals)

    def get_whatsapp_instance(self):
        # When sending message from any object get instance based on provider & conditions
        provider_list = ['gupshup', 'whatsapp_chat_api']
        for provider in provider_list:
            whatsapp_instance_id = self._get_whatsapp_instance(provider)
            if whatsapp_instance_id:
                return whatsapp_instance_id

        if not self._context.get('skip_error'):
            raise UserError(_('Please select atleast one default instance or add %s user in whatsapp instance in users or companies') % self.env.user.name)

    def _get_whatsapp_instance(self, provider):
        # Select instance based on following condition:
        # 1) If current user have whatsapp instance, corresponding provider & whatsapp instance status is enable then return that instance.
        # 2) If instance is not getting from 1st condition then check for company same as user
        # 3) If user, company is not getting from 1st & 2nd condition then we check for default instance
        whatsapp_instance_id = self.sudo().search([('user_ids', '=', self.env.user.id), ('provider', '=', provider),
                                                    ('status', '=', 'enable')], limit=1)

        if whatsapp_instance_id:
            return whatsapp_instance_id
        else:
            whatsapp_instance_id = self.sudo().search([('res_company_ids', '=', self.env.user.company_id.id), ('provider', '=', provider),
                                                        ('status', '=', 'enable')], limit=1)
            if whatsapp_instance_id:
                return whatsapp_instance_id
            else:
                return self._get_default_instance(provider)

    def _get_default_instance(self, provider):
        # Get default instance using following condition:
        # 1) In whatsapp instance search for any instance have default instance true & provider is corresponding provide
        # 2) If not getting instance from 1st condition then we check for whatsapp instance which has status enable
        # 3) If 1st & 2nd condition is not satisfied then raise an user error
        whatsapp_instance_id = self.sudo().search([('default_instance', '=', True), ('provider', '=', provider)], limit=1)
        if whatsapp_instance_id:
            return whatsapp_instance_id
        else:
            whatsapp_instance_id = self.sudo().search([('status', '=', 'enable'), ('provider', '=', provider)], limit=1)
            if whatsapp_instance_id:
                return whatsapp_instance_id
            else:
                return False

    def action_test_connection(self):
        # Checks connection if it is successful or not & add specific message
        if self.provider == 'whatsapp_chat_api':
            try:
                response = requests.request('GET', self.whatsapp_endpoint + '/status?token=' + self.whatsapp_token)
            except Exception as e_log:
                _logger.exception(e_log)
                raise UserError(_('Please add proper whatsapp endpoint or whatsapp token'))
            if response.status_code == 200:
                self.status = 'enable'
                if self.sequence == 'New':
                    self.sequence = self.env['ir.sequence'].next_by_code('whatsapp.instance.sequence')
                return self.wizard_message("CONNECTION SUCCESSFUL")
            elif response.status_code == 401:
                return self.wizard_message("Invalid Credentials")
            else:
                raise Warning("CONNECTION UNSUCCESSFUL")
        elif self.provider == 'gupshup':
            try:
                gupshup_test = 'https://www.gupshup.io/whatsapp/'
                response = requests.request('GET', gupshup_test + self.whatsapp_gupshup_api_key)
            except Exception as e_log:
                _logger.exception(e_log)
                raise UserError(_('Please add proper whatsapp endpoint or whatsapp token'))
            if response.status_code == 200:
                self.status = 'enable'
                if self.sequence == 'New':
                    self.sequence = self.env['ir.sequence'].next_by_code('whatsapp.instance.sequence')
                return self.wizard_message("CONNECTION SUCCESSFUL")
            elif response.status_code == 401:
                return self.wizard_message("Invalid Credentials")
            else:
                raise Warning("CONNECTION UNSUCCESSFUL")

    def wizard_message(self, message):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Message',
            'res_model': 'test.connection.wizard',
            'view_mode': 'form',
            'view_id': self.env['ir.model.data']._xmlid_to_res_id('pragtech_whatsapp_base.test_connection_wizard_form'),
            'context': {'message': message},
            'target': 'new',
            'nodestroy': True,
        }

    def action_whatsapp_instance_disable(self):
        if self.status == 'enable':
            self.status = 'disable'
        return self.status

    def action_import_templates(self):
        # Select provider & import templates
        if self.provider == 'whatsapp_chat_api':
            self.import_template_from_chat_api()
        elif self.provider == 'gupshup':
            self.import_template_from_gupshup()

    def import_template_from_chat_api(self):
        # Import templates from chat api
        url = self.whatsapp_endpoint + '/templates?token=' + self.whatsapp_token
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            for template in response.json()['templates']:
                vals = {'namespace': template['namespace'], 'state': 'post', 'name': template['name'], 'provider': 'whatsapp_chat_api'}
                if template['category']:
                    vals['category'] = template['category']
                for components in template['components']:
                    if components.get('type') == 'HEADER' and 'format' in components:
                        if components['format'] == 'IMAGE':
                            vals.update({'header': 'media_image'})
                        elif components['format'] == 'DOCUMENT':
                            vals.update({'header': 'media_document'})
                        elif components['format'] == 'VIDEO':
                            vals.update({'header': 'media_video'})
                    elif components['type'] == 'BODY':
                        vals.update({'body': components['text']})
                vals.update({'approval_state': template['status'], 'whatsapp_instance_id': self.id})
                language_id = self.env['res.lang'].search(
                    ['|', ('code', '=', template['language']), ('iso_code', '=', template['language']), '|', ('active', '=', True), ('active', '=', False)], limit=1)
                if language_id:
                    vals.update({'languages': language_id.id})
                whatsapp_templates_id = self.env['whatsapp.templates'].sudo().search(
                    [('name', '=', template.get('name')), ('languages', '=', language_id.id), ('provider', '=', 'whatsapp_chat_api')], limit=1)
                if whatsapp_templates_id:
                    whatsapp_template_update_record = whatsapp_templates_id.write(vals)
                    self._cr.commit()
                    if whatsapp_template_update_record:
                        _logger.info("Whatsapp Template is updated into odoo ----------- " + str(whatsapp_templates_id.id))
                else:
                    whatsapp_template_id = self.env['whatsapp.templates'].create(vals)
                    if whatsapp_template_id:
                        _logger.info("Whatsapp Template is created into odoo ----------- " + str(whatsapp_template_id.id))

    def import_template_from_gupshup(self):
        # Import templates from gupshup
        api_key = self.whatsapp_gupshup_api_key
        app_name = self.whatsapp_gupshup_app_name
        if not api_key or not app_name:
            raise UserError(_("Please add Gupshup App Name and Gupshup Api Key"))
        headers = {"Content-Type": "application/x-www-form-urlencoded", "apikey": api_key}
        template_url = "https://api.gupshup.io/sm/api/v1/template/list/" + app_name
        templates = requests.get(template_url, headers=headers)
        if templates.status_code == 200:
            for template in templates.json().get('templates'):
                media_type = 'text'
                gupshup_media_type = template['templateType']
                if gupshup_media_type == 'DOCUMENT':
                    media_type = 'media_document'
                elif gupshup_media_type == 'IMAGE':
                    media_type = 'media_image'
                elif gupshup_media_type == 'VIDEO':
                    media_type = 'media_video'
                meta_example = json.loads(template['meta'])
                values = {
                    'provider': 'gupshup',
                    'whatsapp_instance_id': self.id,
                    'name': template['elementName'],
                    'category': template['category'],
                    'body': template['data'],
                    'template_id': template['id'],
                    'header': media_type,
                    'approval_state': template['status'],
                    'sample_message': template['data'],
                    'gupshup_template_labels': template['vertical'],
                    'namespace': template['namespace'],
                    'gupshup_sample_message': meta_example.get('example')
                }
                if template.get('status') == 'APPROVED':
                    values['state'] = 'post'
                whatsapp_templates_id = self.env['whatsapp.templates'].sudo().search([('name', '=', template['elementName']), ('whatsapp_instance_id', '=', self.id)], limit=1)
                if whatsapp_templates_id:
                    whatsapp_template_update_record = whatsapp_templates_id.write(values)
                    if whatsapp_template_update_record:
                        _logger.info("Whatsapp Template is updated into odoo from gupshup ----------- " + str(whatsapp_templates_id.id))
                else:
                    whatsapp_template_id = self.env['whatsapp.templates'].create(values)
                    if whatsapp_template_id:
                        _logger.info("Whatsapp Template is created into odoo from gupshup----------- " + str(whatsapp_template_id.id))
        return True

    def action_export_templates(self):
        # Export template if template have signature then open wizard & from wizard add current instance signature else export templates
        whatsapp_template_ids = self.env['whatsapp.templates'].sudo().search(
            [('whatsapp_instance_id', '=', self.id), ('approval_state', 'not in', ['approved', 'APPROVED', 'submitted', 'rejected'])])
        template_signature = False
        for whatsapp_template_id in whatsapp_template_ids:
            if whatsapp_template_id.send_template:
                template_signature = True
        if template_signature:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Message',
                'res_model': 'export.template.wizard',
                'view_mode': 'form',
                'view_id': self.env['ir.model.data']._xmlid_to_res_id('pragtech_whatsapp_base.export_template_wizard_form'),
                'target': 'new',
                'nodestroy': True,
            }
        else:
            for whatsapp_template_id in whatsapp_template_ids:
                self.confirm_export_template(whatsapp_template_id)

    def confirm_export_template(self, template_id):
        # Select provider & export templates
        if self.provider == 'whatsapp_chat_api':
            template_id.action_export_template_to_chat_api()

    def action_create_missing_templates(self):
        return True
