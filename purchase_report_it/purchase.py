# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

import datetime

class purchase_order(models.Model):
	_inherit = 'purchase.order'


	@api.one
	def get_confirmado_por_cc(self):
		self.env.cr.execute(""" select mm.author_id from mail_message mm 
inner join mail_message_subtype mms on mms.id = mm.subtype_id
where mm.model = 'purchase.order' and res_id = """ +str(self.id)+ """
and mms.name = 'RFQ Confirmed'
 """)
		resultado = False
		for i in self.env.cr.fetchall():
			resultado = i[0]
		self.confirmado_por_cc = resultado


	@api.one
	def get_aprobado_por_cc(self):
		self.env.cr.execute(""" select mm.author_id from mail_message mm 
inner join mail_message_subtype mms on mms.id = mm.subtype_id
where mm.model = 'purchase.order' and res_id = """ +str(self.id)+ """
and mms.name = 'RFQ Approved'
 """)
		resultado = False
		for i in self.env.cr.fetchall():
			resultado = i[0]
		self.aprobado_por_cc = resultado



	aprobado_por_cc = fields.Many2one('res.partner','Aprobado Por',compute='get_aprobado_por_cc')
	confirmado_por_cc = fields.Many2one('res.partner','Confirmado Por',compute='get_confirmado_por_cc')
	contacto_id = fields.Many2one('res.partner','Contacto')
	telefono_contacto = fields.Char('Telefono Contacto',related='contacto_id.phone')
	celular_contacto = fields.Char('Celular Contacto',related='contacto_id.mobile')


	def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
		t = super(purchase_order,self).onchange_partner_id(cr, uid, ids, partner_id, context)

		cont = self.pool.get('res.partner').search(cr,uid,[('parent_id','=',partner_id)],context=context)
		if len(cont)>0 and 'value' in t:
			t['value']['contacto_id'] = cont[0]
		return t