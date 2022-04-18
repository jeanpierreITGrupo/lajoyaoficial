# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv


class purchase_order(models.Model):
	_inherit = 'purchase.order'

	sup_account = fields.Many2one('account.account', 'Cuenta', related='partner_id.property_account_payable')
	sup_phone = fields.Char('Teléfono', related='partner_id.phone')
	sup_email = fields.Char('E-mail', related='partner_id.email')
	sup_contact = fields.Char('Contacto', related='partner_id.ref')