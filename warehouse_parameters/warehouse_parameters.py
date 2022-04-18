# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import openerp.addons.decimal_precision as dp

import datetime

class warehouse_parameters(models.Model):
	_name = 'warehouse.parameters'
	_rec_name = 'name'

	name = fields.Char('Nombre',size=50, default='Parametros Generales')

	def init(self, cr):
		cr.execute('select id from res_users')
		uid = cr.dictfetchall()
		cr.execute('select id from warehouse_parameters')
		ids = cr.fetchall()
		
		if len(ids) == 0:
			cr.execute("""INSERT INTO warehouse_parameters (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Parametros Generales');""")