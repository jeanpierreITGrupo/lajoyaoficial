# -*- encoding: utf-8 -*-
from openerp.osv import osv
from tempfile    import TemporaryFile
from openerp     import models, fields, api
import csv
import base64
import codecs
import datetime
import openerp.addons.decimal_precision as dp

class adelantos_importador(models.Model):
	_name = 'adelantos.importador'

	period_id    = fields.Many2one('account.period', 'Periodo', required=True)
	name         = fields.Char('Nombre',size=50, default='Importar Adelantos')
	product_file = fields.Binary('Adelantos (CSV)')
	delimiter    = fields.Char('Delimitador')
	imported 	 = fields.Boolean('importado', default=False)
	state 		 = fields.Selection([('draft','Borrador'),('not_imported','No Importado'),('imported',"Importado")], 'Estado', default="draft")

	noimp_lines = fields.One2many('adelantos.no.importado','importador_id','lineas')

	# def init(self, cr):
	# 	cr.execute('select id from res_users')
	# 	uid = cr.dictfetchall()
	# 	cr.execute('select id from adelantos_importador')
	# 	ids = cr.fetchall()
		
	# 	if len(ids) == 0:
	# 		cr.execute("""INSERT INTO adelantos_importador (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Importar Adelantos');""")

	@api.one
	def show_file_fields(self):
		self.state = 'not_imported'

	@api.one
	def unlink(self):
		if self.imported:
			raise osv.except_osv('Alerta!', 'No se puede eliminar el importador del periodo '+self.period_id.code+'.\nExiste una importación con este periodo')
		t = super(adelantos_importador, self).unlink()
		return t

	@api.model
	def create(self, vals):
		ti = self.env['adelantos.importador'].search([('period_id','=',vals['period_id'])])
		if len(ti):
			ap = self.env['account.period'].search([('id','=',vals['period_id'])])[0]
			raise osv.except_osv('Alerta!', 'Ya existe un importador para el periodo '+ap.code)
		return super(adelantos_importador, self).create(vals)

	@api.one
	def write(self, vals):
		t = super(adelantos_importador, self).write(vals)
		self.refresh()
		ti = self.env['adelantos.importador'].search([('period_id','=',self.period_id.id)])
		if len(ti) > 1:
			raise osv.except_osv('Alerta!', 'Ya existe un importador para el periodo '+self.period_id.code)
		return t

	def string2float(self, s):
		try:
			float(s)
			return True
		except:
			return False

	@api.one
	def import_adelantos(self):
		if self.product_file == None:
			raise osv.except_osv('Alerta!', 'Debe cargar un archivo csv.')
		elif not self.delimiter:
			raise osv.except_osv('Alerta!', 'Debe seleccionar un delimitador.')
		else:
			self.env.cr.execute("set client_encoding ='UTF8';")
			data = self.read()[0]
			fileobj = TemporaryFile('w+')
			fileobj.write(base64.decodestring(data['product_file']))
			fileobj.seek(0)
			c=base64.decodestring(data['product_file'])
			fic = csv.reader(fileobj,delimiter=str(self.delimiter),quotechar='"')

			skip_titles = True
			for row in fic:
				if skip_titles:
					skip_titles = False
					continue
				detalle = ""

				# VALIDACIONES
				if not len(self.env['account.period'].search([('code','=',row[0].strip())])): #SI NO HAY PERIODO CONTABLE
					detalle += u"- periodo contable incorrecto\n"
				if not len(self.env['hr.employee'].search([('identification_id','=',row[1].strip())])): #SI NO HAY DNI
					detalle += u"- dni incorrecto\n"
				if not len(row[2].strip()): #SI NO HAY MOTIVO
					detalle += u"- motivo incorrecto\n"
				if not self.string2float(row[3].strip()): #SI NO HAY MONTO
					detalle += u"- monto incorrecto\n"
				if not len(row[4].strip()): #SI NO HAY FECHA
					detalle += u"- fecha incorrecta\n"
				else:
					if len(row[4].strip().split("/")) != 3:
						detalle += u"- fecha incorrecta\n"
				if not len(row[7].strip()): #SI NO HAY TIPO ADELANTO
					detalle += u"- tipo de adelanto incorrecto\n"
				if not len(row[8].strip()): #SI NO HAY CUENTA
					detalle += u"- cuenta incorrecta\n"
				else:
					if not len(self.env['account.account'].search([('code','=',row[8].strip())])):
						detalle += u"- cuenta incorrecta\n"

				if len(detalle):
					vals = {
						'importador_id': self.id,

						'period_id'    : row[0],
						'dni'          : row[1],
						'motivo'       : row[2],
						'monto'        : row[3],
						'fecha'        : row[4],
						'observacion_1': row[5],
						'observacion_2': row[6],
						'adelanto_id'  : row[7],
						'account_id'   : row[8],
						'detalle'      : detalle,

					}
					self.env['adelantos.no.importado'].create(vals)
				else:
					# VALIDACIONES SECUNDARIAS
					new_adelanto = {}

					ap = self.env['account.period'].search([('code','=',row[0].strip())])[0]
					new_adelanto['period_id'] = ap.id

					he = self.env['hr.employee'].search([('identification_id','=',row[1].strip())])[0]
					new_adelanto['employee'] = he.id

					new_adelanto['motivo'] = row[2].strip()

					new_adelanto['monto'] = float(row[3].strip())

					f = row[4].strip().split("/")
					f = datetime.datetime.strptime(f[2]+"-"+f[1]+"-"+f[0],"%Y-%m-%d")
					new_adelanto['fecha'] = f

					new_adelanto['observacion_1'] = row[5].strip()
					new_adelanto['observacion_2'] = row[6].strip()

					hta = self.env['hr.table.adelanto'].search([('name','=',row[7].strip())])
					aa = self.env['account.account'].search([('code','=',row[8].strip())])[0]
					if len(hta):
						hta = hta[0]
						hta.account_id = aa.id
					else:
						hta = self.env['hr.table.adelanto'].create({'name':row[7].strip(), 'account_id':aa.id})
					new_adelanto['adelanto_id'] = hta.id
					ha = self.env['hr.adelanto'].create(new_adelanto)
		self.imported = True
		self.state = 'imported'

	@api.one
	def procesar(self):
		for line in self.noimp_lines:
			# VALIDACIONES SECUNDARIAS
			detalle = ""

			if line.period_id:
				if not len(self.env['account.period'].search([('code','=',line.period_id.strip())])): #SI NO HAY PERIODO CONTABLE
					detalle += u"- periodo contable incorrecto\n"
			if line.dni:
				if line.dni and not len(self.env['hr.employee'].search([('identification_id','=',line.dni.strip())])): #SI NO HAY DNI
					detalle += u"- dni incorrecto\n"
			if line.motivo and not len(line.motivo.strip()): #SI NO HAY MOTIVO
				detalle += u"- motivo incorrecto\n"
			if line.monto:
				if not self.string2float(line.monto.strip()): #SI NO HAY MONTO
					detalle += u"- monto incorrecto\n"
			if line.fecha and not len(line.fecha.strip()): #SI NO HAY FECHA
				detalle += u"- fecha incorrecta\n"
			else:
				if len(line.fecha.strip().split("/")) != 3:
					detalle += u"- fecha incorrecta\n"
			if line.adelanto_id and not len(line.adelanto_id.strip()): #SI NO HAY TIPO ADELANTO
				detalle += u"- tipo de adelanto incorrecto\n"
			if line.account_id and not len(line.account_id.strip()): #SI NO HAY CUENTA
				detalle += u"- cuenta incorrecta\n"
			else:
				if not len(self.env['account.account'].search([('code','=',line.account_id.strip())])):
					detalle += u"- cuenta incorrecta\n"

			if len(detalle):
				self.detalle = detalle
			else:
				new_adelanto = {}

				ap = self.env['account.period'].search([('code','=',line.period_id.strip())])[0]
				new_adelanto['period_id'] = ap.id

				he = self.env['hr.employee'].search([('identification_id','=',line.dni.strip())])[0]
				new_adelanto['employee'] = he.id

				new_adelanto['motivo'] = line.motivo.strip()

				new_adelanto['monto'] = float(line.monto.strip())

				f = line.fecha.strip().split("/")
				f = datetime.datetime.strptime(f[2]+"-"+f[1]+"-"+f[0],"%Y-%m-%d")
				new_adelanto['fecha'] = f

				new_adelanto['observacion_1'] = line.observacion_1.strip()
				new_adelanto['observacion_2'] = line.observacion_2.strip()

				hta = self.env['hr.table.adelanto'].search([('name','=',line.adelanto_id.strip())])
				aa = self.env['account.account'].search([('code','=',line.account_id.strip())])[0]
				if len(hta):
					hta = hta[0]
					hta.account_id = aa.id
				else:
					hta = self.env['hr.table.adelanto'].create({'name':line.adelanto_id.strip(), 'account_id':aa.id})
				new_adelanto['adelanto_id'] = hta.id
				ha = self.env['hr.adelanto'].create(new_adelanto)

				line.unlink()


	@api.one
	def clean(self):
		for i in self.noimp_lines:
			i.unlink()

class adelantos_no_importado(models.Model):
	_name = 'adelantos.no.importado'

	importador_id = fields.Many2one('adelantos.importador','importador Padre')

	period_id     = fields.Char(u'Periodo Contable')
	dni           = fields.Char(u'Dni')
	motivo        = fields.Char(u'Motivo')
	monto         = fields.Char(u'Monto')
	fecha         = fields.Char(u'Fecha')
	observacion_1 = fields.Char(u'Observación 1')
	observacion_2 = fields.Char(u'Observación 2')
	adelanto_id   = fields.Char(u'Tipo de Adelanto')
	account_id    = fields.Char(u'Cuenta')
	detalle       = fields.Char(u'Detalle')