# -*- coding: utf-8 -*-

from openerp import models, fields, api

from openerp import http


class main_parameter(models.Model):
	_name = 'main.parameter'

	def init(self, cr):
		cr.execute('select id from res_users')
		uid = cr.dictfetchall()
		print 'uid', uid
		print 'uid0', uid[0]['id']
		cr.execute('select id from main_parameter')
		ids = cr.fetchall()
		
		print 'ids', ids
		
		if len(ids) == 0:
			cr.execute("""INSERT INTO main_parameter (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Parametros Generales');""")
	
	name = fields.Char('Nombre',size=50, default='Parametros Generales')
	deliver_account_mn = fields.Many2one('account.account','Rendicion Moneda Nacional')
	deliver_account_me = fields.Many2one('account.account','Rendicion Moneda Extranjera')
	loan_account_mn = fields.Many2one('account.account','Cuenta Prestamos')
	loan_account_me = fields.Many2one('account.account','Cuenta Prestamos M.E.')
	loan_journal_mn = fields.Many2one('account.journal','Diario Rendiciones M.N.')
	loan_journal_me = fields.Many2one('account.journal','Diario Rendiciones M.E.')
	export_document_id = fields.Many2one('it.type.document', string="Documento de Exportacion",index=True,ondelete='restrict')
	no_home_document_id = fields.Many2one('it.type.document', string="Comprobante de Pago No domiciliado",index=True,ondelete='restrict')
	no_home_debit_document_id = fields.Many2one('it.type.document', string="N. Debito no domiciliado",index=True,ondelete='restrict')
	no_home_credit_document_id = fields.Many2one('it.type.document', string="N. Credito no domiciliado",index=True,ondelete='restrict')
	
	sunat_type_document_ruc_id = fields.Many2one('it.type.document.partner', string="Tipo de Documento RUC",index=True,ondelete='restrict')
	l_ruc = fields.Integer(string="Longitud RUC")
	
	sunat_type_document_dni_id = fields.Many2one('it.type.document.partner', string="Tipo de Documento DNI",index=True,ondelete='restrict')
	l_dni = fields.Integer(string="Longitud DNI")
	
	sequence_gvinculado = fields.Many2one('ir.sequence', string='Secuencia para Gasto Vinculado')

	template_account_contable= fields.Many2one('account.chart.template','Código Plan de Cuentas')

	partner_null_id = fields.Many2one('res.partner','Partner para Anulaciones')
	partner_venta_boleta  = fields.Many2one('res.partner','Partner para Ventas Boleta')

	dir_create_file = fields.Char('Directorio Exportadores', size=100)

	dir_ple_create_file = fields.Char('Directorio PLE', size=100)


	account_anticipo_proveedor_mn = fields.Many2one('account.account','Cuenta Anticipo Proveedor M.N.')
	account_anticipo_proveedor_me = fields.Many2one('account.account','Cuenta Anticipo Proveedor M.E.')
	account_anticipo_clientes_mn = fields.Many2one('account.account','Cuenta Anticipo Cliente M.N.')
	account_anticipo_clientes_me = fields.Many2one('account.account','Cuenta Anticipo Cliente M.E.')

	account_perception_igv = fields.Many2one('account.tax.code','Cuenta de Impuesto')
	account_perception_tipo_documento = fields.Many2one('it.type.document','Tipo de Documento')

	diario_destino = fields.Many2one('account.journal','Diario Destino')

	@api.onchange('dir_ple_create_file')
	def onchange_dir_create_file(self):
		if self.dir_ple_create_file:
			if self.dir_ple_create_file[-1] == '/':
				pass
			else:
				self.dir_ple_create_file = self.dir_ple_create_file + '/'

	
	@api.onchange('dir_create_file')
	def onchange_dir_create_file(self):
		if self.dir_create_file:
			if self.dir_create_file[-1] == '/':
				pass
			else:
				self.dir_create_file = self.dir_create_file + '/'
