# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp import http


class corrector_linea_compra_adquisicion(models.Model):
	_name = 'corrector.linea.compra.adquisicion'

	libro = fields.Many2one('account.journal','Libro')
	corrector_id = fields.Many2one('corrector.ple.compra','Corrector')


class corrector_linea_compra_anulado(models.Model):
	_name = 'corrector.linea.compra.anulado'

	libro = fields.Many2one('account.journal','Libro')
	estado = fields.Char('Estado')
	corrector_id = fields.Many2one('corrector.ple.compra','Corrector')

class corrector_linea_compra_estadodocumento(models.Model):
	_name = 'corrector.linea.compra.estadodocumento'

	documento = fields.Many2one('it.type.document','Tipo Documento')
	libro = fields.Many2one('account.journal','Libro')
	estado = fields.Char('Estado')
	corrector_id = fields.Many2one('corrector.ple.compra','Corrector')


class corrector_linea_compra_estadofecha(models.Model):
	_name = 'corrector.linea.compra.estadofecha'

	documento = fields.Many2one('it.type.document','Tipo Documento')
	libro = fields.Many2one('account.journal','Libro')
	estado = fields.Char('Estado')
	corrector_id = fields.Many2one('corrector.ple.compra','Corrector')

class corrector_ple_compra(models.Model):
	_name = 'corrector.ple.compra'	

	period_id = fields.Many2one('account.period','Periodo',required=True)
	anulados = fields.One2many('corrector.linea.compra.anulado','corrector_id',string='Anulados')
	estado_documento = fields.One2many('corrector.linea.compra.estadodocumento','corrector_id','Estado Documento')
	adquisicion = fields.One2many('corrector.linea.compra.adquisicion','corrector_id','Adquisición')
	fecha = fields.One2many('corrector.linea.compra.estadofecha','corrector_id','Fecha')

	anulados_mal = fields.Integer('Por Corregir Anulados')
	estadodocumento_mal = fields.Integer('Por Corregir Estado Documento')
	adquisicion_mal = fields.Integer('Por Corregir Adquisicion')
	fecha_mal = fields.Integer('Por Corregir Fecha')

	adquisicion_check = fields.Boolean('Mantener Tipo de Adquisición',default=True)

	@api.one
	def calcular(self):
		conta= 0
		parametros= self.env['main.parameter'].search([])[0]		
		for i in self.anulados:
			self.env.cr.execute(""" 
					select *  from account_move 
							where period_id = """ +str(self.period_id.id)+ """
							and journal_id = """ +str(i.libro.id)+ """
							and partner_id = """ +str(parametros.partner_null_id.id)+ """
							and ple_compra != '""" +i.estado+ """'
					""")
			conta += len(self.env.cr.fetchall())

		self.anulados_mal = conta

		#####
		conta = 0
		for i in self.adquisicion:
			self.env.cr.execute(""" 
				select am.id from
				account_move am
				where am.period_id = """ +str(self.period_id.id)+ """
				and am.journal_id = """ +str(i.libro.id)+ """				
				and  (am.tipo_adquisicion = '' or  am.tipo_adquisicion is null )
				""")
			conta += len(self.env.cr.fetchall())
		self.adquisicion_mal = conta

		#####
		conta = 0

		for i in self.estado_documento:
			self.env.cr.execute(""" 
				select * from  account_move 
						where period_id = """ +str(self.period_id.id)+ """
						and journal_id = """ +str(i.libro.id)+ """						
						and dec_reg_type_document_id = """ +str(i.documento.id)+ """
						and ple_compra != '""" +i.estado+ """'
						
				""")
			conta += len(self.env.cr.fetchall())
		self.estadodocumento_mal = conta

		######
		conta = 0

		for i in self.fecha:
			self.env.cr.execute(""" 
				select * from  account_move 
						where period_id = """ +str(self.period_id.id)+ """
						and journal_id = """ +str(i.libro.id)+ """						
						and dec_reg_type_document_id = """ +str(i.documento.id)+ """
						and date < '""" + str(self.period_id.date_start) + """'
						and ple_compra != '""" +i.estado+ """'
						
				""")
			conta += len(self.env.cr.fetchall())
		self.fecha_mal = conta


	@api.one
	def reparar(self):
		self.corregir_anulados()
		self.corregir_adquisicion()
		self.corregir_estadodocumento()
		self.corregir_estadofecha()
		self.calcular()




	@api.one
	def corregir_anulados(self):
		parametros= self.env['main.parameter'].search([])[0]		
		for i in self.anulados:
			self.env.cr.execute(""" 
					UPDATE account_move SET
							ple_compra = '""" +i.estado+ """'
							where period_id = """ +str(self.period_id.id)+ """
							and journal_id = """ +str(i.libro.id)+ """
							and partner_id = """ +str(parametros.partner_null_id.id)+ """
					""")


	@api.one
	def corregir_adquisicion(self):		
		for i in self.adquisicion:
			self.env.cr.execute(""" 
				select am.id from
				account_move am
				where am.period_id = """ +str(self.period_id.id)+ """
				and am.journal_id = """ +str(i.libro.id)+ """				
				""")
			t = self.env.cr.fetchall()
			for j in t:
					tipo_tmp = ""
					self.env.cr.execute("""
					select aa.tipo_adquisicion_diario from
					account_move am
					inner join account_move_line aml on aml.move_id = am.id
					inner join account_account aa on aa.id = aml.account_id
					where left(code,1) != '4'
					and am.period_id = """ +str(self.period_id.id)+ """
					and am.journal_id = """ +str(i.libro.id)+ """
					and am.id = """ +str(j[0])+ """
					""")
					for w in self.env.cr.fetchall():
						tipo_tmp = w[0] if w[0] else ''

					self.env.cr.execute(""" 
						UPDATE account_move SET
						tipo_adquisicion = '""" +tipo_tmp+ """'
						where id = """ +str(j[0])+ """
						""" + "and (tipo_adquisicion is null or tipo_adquisicion = '' )" if self.adquisicion_check else '' + """
						""")

	@api.one
	def corregir_estadodocumento(self):		
		for i in self.estado_documento:
			self.env.cr.execute(""" 
				UPDATE account_move SET
						ple_compra = '""" +i.estado+ """'
						where period_id = """ +str(self.period_id.id)+ """
						and journal_id = """ +str(i.libro.id)+ """						
						and dec_reg_type_document_id = """ +str(i.documento.id)+ """
				""")


	@api.one
	def corregir_estadofecha(self):		
		for i in self.fecha:
			self.env.cr.execute(""" 
				UPDATE account_move SET
						ple_compra = '""" +i.estado+ """'
						where period_id = """ +str(self.period_id.id)+ """
						and journal_id = """ +str(i.libro.id)+ """						
						and dec_reg_type_document_id = """ +str(i.documento.id)+ """
						and date < '""" + str(self.period_id.date_start) + """'
				""")






















class corrector_linea_venta_estadofecha(models.Model):
	_name = 'corrector.linea.venta.estadofecha'

	documento = fields.Many2one('it.type.document','Tipo Documento')
	libro = fields.Many2one('account.journal','Libro')
	estado = fields.Char('Estado')
	corrector_id = fields.Many2one('corrector.ple.compra','Corrector')




class corrector_linea_venta_anulado(models.Model):
	_name = 'corrector.linea.venta.anulado'

	libro = fields.Many2one('account.journal','Libro')
	estado = fields.Char('Estado')
	corrector_id = fields.Many2one('corrector.ple.venta','Corrector')

class corrector_linea_venta_estadodocumento(models.Model):
	_name = 'corrector.linea.venta.estadodocumento'

	documento = fields.Many2one('it.type.document','Tipo Documento')
	libro = fields.Many2one('account.journal','Libro')
	estado = fields.Char('Estado')
	corrector_id = fields.Many2one('corrector.ple.venta','Corrector')

class corrector_ple_venta(models.Model):
	_name = 'corrector.ple.venta'	

	period_id = fields.Many2one('account.period','Periodo',required=True)
	anulados = fields.One2many('corrector.linea.venta.anulado','corrector_id','Anulados')
	estado_documento = fields.One2many('corrector.linea.venta.estadodocumento','corrector_id','Estado Documento')
	fecha = fields.One2many('corrector.linea.venta.estadofecha','corrector_id','Fecha')


	anulados_mal = fields.Integer('Por Corregir Anulados')
	estadodocumento_mal = fields.Integer('Por Corregir Estado Documento')
	fecha_mal = fields.Integer('Por Corregir Fecha')


	@api.one
	def calcular(self):
		conta= 0
		parametros= self.env['main.parameter'].search([])[0]		
		for i in self.anulados:
			self.env.cr.execute(""" 
					select *  from account_move 
							where period_id = """ +str(self.period_id.id)+ """
							and journal_id = """ +str(i.libro.id)+ """
							and partner_id = """ +str(parametros.partner_null_id.id)+ """
							and ple_venta != '""" +i.estado+ """'
					""")
			conta += len(self.env.cr.fetchall())

		self.anulados_mal = conta

		#####
		conta = 0

		for i in self.estado_documento:
			self.env.cr.execute(""" 
				select * from  account_move 
						where period_id = """ +str(self.period_id.id)+ """
						and journal_id = """ +str(i.libro.id)+ """						
						and dec_reg_type_document_id = """ +str(i.documento.id)+ """
						and ple_venta != '""" +i.estado+ """'
						
				""")
			conta += len(self.env.cr.fetchall())
		self.estadodocumento_mal = conta

		######
		conta = 0

		for i in self.fecha:
			self.env.cr.execute(""" 
				select * from  account_move 
						where period_id = """ +str(self.period_id.id)+ """
						and journal_id = """ +str(i.libro.id)+ """						
						and dec_reg_type_document_id = """ +str(i.documento.id)+ """
						and date < '""" + str(self.period_id.date_start) + """'
						and ple_venta != '""" +i.estado+ """'
						
				""")
			conta += len(self.env.cr.fetchall())
		self.fecha_mal = conta


	@api.one
	def reparar(self):
		self.corregir_anulados()
		self.corregir_estadodocumento()
		self.corregir_estadofecha()
		self.calcular()


	@api.one
	def corregir_anulados(self):
		parametros= self.env['main.parameter'].search([])[0]		
		for i in self.anulados:
			self.env.cr.execute(""" 
				UPDATE account_move SET
						ple_venta = '""" +i.estado+ """'
						where period_id = """ +str(self.period_id.id)+ """
						and journal_id = """ +str(i.libro.id)+ """
						and partner_id = """ +str(parametros.partner_null_id.id)+ """
				""")

	@api.one
	def corregir_estadodocumento(self):		
		for i in self.estado_documento:
			self.env.cr.execute(""" 
				UPDATE account_move SET
						ple_venta = '""" +i.estado+ """'
						where period_id = """ +str(self.period_id.id)+ """
						and journal_id = """ +str(i.libro.id)+ """						
						and dec_reg_type_document_id = """ +str(i.documento.id)+ """
				""")

	@api.one
	def corregir_estadofecha(self):		
		for i in self.fecha:
			self.env.cr.execute(""" 
				UPDATE account_move SET
						ple_venta = '""" +i.estado+ """'
						where period_id = """ +str(self.period_id.id)+ """
						and journal_id = """ +str(i.libro.id)+ """						
						and dec_reg_type_document_id = """ +str(i.documento.id)+ """
						and date < '""" + str(self.period_id.date_start) + """'
				""")



