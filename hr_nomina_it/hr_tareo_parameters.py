# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api

class hr_tareo_parameters(models.Model):
	_name     = 'hr.tareo.parameters'
	_rec_name = 'name'
	
	name         = fields.Char(u'Parametros tareo')
	asignacion_f = fields.Boolean(u'Asignación familiar', default=False)

	def init(self, cr):
		cr.execute('select id from hr_tareo_parameters')
		ids = cr.fetchall()

		if len(ids) == 0:
			cr.execute("""INSERT INTO hr_tareo_parameters (name) VALUES ('Parametros tareo')""")