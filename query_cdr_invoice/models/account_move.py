import base64
import zipfile
from io import BytesIO
from xml.etree import ElementTree

from lxml import etree
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from zeep import Client, Settings
from zeep.transports import Transport


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_query_cdr_invoice(self):
        company = self.company_id
        provider = company.l10n_pe_edi_provider
        edi_format = self.env.ref('l10n_pe_edi.edi_pe_ubl_2_1')
        try:
            credentials = getattr(edi_format, '_l10n_pe_edi_get_%s_credentials' % provider)(company)
            if provider == 'sunat':
                credentials['wsdl'] = "https://e-factura.sunat.gob.pe/ol-it-wsconscpegem/billConsultService?wsdl"

        except Exception as error:
            raise ValidationError(f'Error al tratar de obtener credenciales: {error}')

        try:
            data, response = self.get_status_cdr_sunat(credentials, company)
            self.set_status_cdr_sunat(data, response)
        except Exception as error:
            raise ValidationError(f'Error al trata de enviar y/o recepcionar el cdr :{error}')

    def get_status_cdr_sunat(self, credentials, company):
        self.ensure_one()
        transport = Transport(operation_timeout=30, timeout=30)
        settings = Settings(raw_response=True)

        client = Client(
            wsdl=credentials['wsdl'],
            wsse=credentials['token'],
            settings=settings,
            transport=transport,
        )
        reference = self.name
        vat_company = company.vat
        select = reference.find('-')
        data = {
            'rucComprobante': vat_company,
            'tipoComprobante': self.l10n_latam_document_type_id.code,
            'serieComprobante': reference[:select].replace(" ", ""),
            'numeroComprobante': reference[select + 1:].replace(" ", ""),
        }

        result = client.service.getStatusCdr(
            rucComprobante=data['rucComprobante'],
            tipoComprobante=data['tipoComprobante'],
            serieComprobante=data['serieComprobante'],
            numeroComprobante=data['numeroComprobante']
        )
        result.raise_for_status()
        cdr = result.content
        cdr_tree = ElementTree.fromstring(cdr)
        response = cdr_tree.findall('{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://service.sunat.gob.pe}getStatusCdrResponse/statusCdr/*')
        return data, response

    def set_status_cdr_sunat(self, data, response):
        zip_edi_str = response[0].text
        cdr_code_response, cdr_msg_response = self.get_cdr_code_msj_sunat_response(zip_edi_str)

        if 4000 <= cdr_code_response:
            message = "El documento de facturación fue aceptado con observaciones por la SUNAT"
            temp = 1

        elif 2000 <= cdr_code_response < 4000:
            message = "El documento de facturación fue rechazada por la SUNAT"
            temp = 2

        elif 100 <= cdr_code_response < 2000:
            message = "Se ha dado una excepcion por parte del proceso de SUNAT"
            temp = 3

        else:
            message = "El documento de facturación fue aceptado correctamente por la SUNAT"
            temp = 1

        edi_filename = f'{data["rucComprobante"]}-CDR-{data["serieComprobante"]}-{data["numeroComprobante"]}'
        self._print_cdr_zip(edi_filename, zip_edi_str, message)

        if temp == 1:
            self._change_state_edi()
        elif temp == 2:
            self._change_state_edi_cancelled()
        else:
            self._change_state_edi_to_cancel()

    def get_cdr_code_msj_sunat_response(self, res):
        if isinstance(res, str):
            res = base64.b64decode(res)
        xml_response = ""
        with zipfile.ZipFile(BytesIO(res)) as z:
            for archive in z.namelist():
                if "xml" in archive:
                    xml_response = z.read(archive)
        tree_xml_response = etree.fromstring(xml_response)
        xml_namespace = "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}"
        code_response = tree_xml_response.findall('{0}DocumentResponse/{0}Response/*'.format(xml_namespace))[1].text
        msg_response = tree_xml_response.findall('{0}DocumentResponse/{0}Response/*'.format(xml_namespace))[2].text
        return int(code_response), msg_response

    def _change_state_edi(self):
        self.edi_document_ids.write({
            'state': 'sent',
            'error': False
        })

    def _change_state_edi_to_cancel(self):
        self.edi_document_ids.write({
            'state': 'to_cancel',
            'error': True
        })
        self.button_draft()
        self.button_cancel()

    def _change_state_edi_cancelled(self):
        self.edi_document_ids.write({
            'state': 'cancelled',
            'error': True
        })
        self.button_draft()
        self.button_cancel()

    def _print_cdr_zip(self, edi_filename, zip_edi_str, message):
        attachment_id = self.env['ir.attachment'].create({
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'name': '%s.zip' % edi_filename,
            'datas': bytes(zip_edi_str, 'utf-8'),
            'mimetype': 'application/zip'
        })
        message = _(message)
        self.with_context(no_new_invoice=True).message_post(
            body=message,
            attachment_ids=[attachment_id.id],
        )
