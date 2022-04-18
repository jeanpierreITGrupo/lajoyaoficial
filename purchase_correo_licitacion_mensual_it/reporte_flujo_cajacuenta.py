# -*- coding: utf-8 -*-
from openerp     import models, fields, api
from openerp.osv import osv
import base64
import decimal

class purchase_parameter(models.Model):
	_inherit = 'purchase.parameter'

	activar_correo_licitaciones = fields.Boolean('Enviar correo al crear licitaciones')

class licitacion_advance(models.Model):
	_inherit = 'licitacion.advance'

	@api.model
	def create(self,vals):
		t = super(licitacion_advance,self).create(vals)

		pp = self.env['purchase.parameter'].search([])[0]
		if pp.activar_correo_licitaciones:
			values              = {}
			values['subject']   = " / ".join([t.number, t.area.name, t.solicitante.name_related])
			values['email_to']  = "imartel.pagos@lajoyamining.com"
			values['body_html'] = u"<h1>La Joya Minning</h1><br/>\
									<h1>Licitación Mensual</h1> <br/>\
								  	<ul>\
								  		<li><h2>Licitación Mensual: " + t.number + u"</h2></li>\
								  		<li><h2>Área: " + t.area.name + u"</h2></li>\
								  		<li><h2>Solicitante: " + t.solicitante.name_related + u"</h2></li>\
								  	</ul>\
								  	<h3>Link:</he><br/>\
								  	http://179.43.96.110:8069/web?db=" + self.env.cr.dbname + u"#id=" + str(t.id) + u"&view_type=form&model=licitacion.advance&menu_id=701&action=882"
			values['res_id']    = False

			msg_id = self.env['mail.mail'].create(values)
			if msg_id:
				msg_id.send()

		return t