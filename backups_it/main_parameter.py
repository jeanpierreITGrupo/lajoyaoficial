# -*- coding: utf-8 -*-

from openerp import models, fields, api

from openerp import http
from openerp.http import request

class utilitario_parameter(models.Model):
	_name = 'utilitario.parameter'

	def init(self, cr):
		cr.execute('select id from res_users')
		uid = cr.dictfetchall()
		print 'uid', uid
		print 'uid0', uid[0]['id']
		cr.execute('select id from utilitario_parameter')
		ids = cr.fetchall()
		
		print 'ids', ids
		
		if len(ids) == 0:
			cr.execute("""INSERT INTO utilitario_parameter (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Parametros Generales');""")
	
	name = fields.Char('Nombre',size=50, default='Parametros Generales')

	directorio = fields.Char('Directorio')

	@api.onchange('directorio')
	def onchange_dir_create_file(self):
		if self.directorio:
			if self.directorio[-1] == '/':
				pass
			else:
				self.directorio = self.directorio + '/'


class backup_utilitario(models.Model):
	_name = 'backup.utilitario'

	@api.one
	def generar_backup(self):
		import os
		import datetime
		param = self.env['utilitario.parameter'].search([])[0]
		os.system("pg_dump --dbname=postgresql://openpg:openpgpwd@127.0.0.1:5432/Lajoya_2017 --format tar --blobs --encoding UTF8 --verbose > "  + param.directorio  + "backup_" + str(datetime.datetime.now()) + ".backup" )
