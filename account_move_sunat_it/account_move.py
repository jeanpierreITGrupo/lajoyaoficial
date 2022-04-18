# -*- coding: utf-8 -*-

from openerp import models, fields, api , exceptions , _

class account_move(models.Model):
	_inherit = 'account.move'
	optative_ple = fields.Boolean('Anotación optativa para PLE')


	@api.v8
	@api.one
	def compute_verify_account_invoice(self):
		if len(self.env['account.invoice'].search([('move_id','=',self.id)]))>0:
			self.verify_account_invoice_exist = True
		else:
			self.verify_account_invoice_exist = False

	dec_reg_type_document_id = fields.Many2one('it.type.document', string="Tipo de Documento",ondelete='restrict')
	dec_reg_nro_comprobante = fields.Char('Comprobante', size=30)

	dec_mod_type_document_id = fields.Many2one('it.type.document', string="Tipo de Documento",ondelete='restrict')
	dec_mod_nro_comprobante = fields.Char('Comprobante', size=30)
	dec_mod_fecha = fields.Date('Fecha', size=30)
	dec_mod_base_imponible = fields.Float('Base Imponible', digits=(12,2))
	dec_mod_igv = fields.Float('IGV', digits=(12,2))
	dec_mod_total = fields.Float('Total', digits=(12,2))
	
	com_det_code_operation = fields.Char('Codigo de Operación',size=50)
	com_det_date = fields.Date('Fecha')
	com_det_amount =fields.Float('Monto', digits=(12,2))
	com_det_number = fields.Char('Número', size=50)
	com_det_date_maturity = fields.Date('Fecha Vencimiento')
	com_det_type_change = fields.Float('Tipo de Cambio', digits=(16,3))
	com_det_currency = fields.Many2one('res.currency', string="Moneda")
	verify_account_invoice_exist = fields.Boolean('Existe Factura?', compute='compute_verify_account_invoice')

	nro_formulario_compra_externa = fields.Char('Nro. Formulario Compra Externa')
	codigo_aduana = fields.Char('Codigo Aduana Sunat')


	dec_percep_tipo_tasa_percepcion = fields.Char('Tipo Tasa')
	dec_percep_numero_serie = fields.Char(u'Número de Documento')

	@api.one
	@api.constrains('dec_reg_nro_comprobante')
	def constrains_dec_reg_nro_comprobante(self):
		print "llego constraint acount_move"
		if self.dec_reg_nro_comprobante:
			filtro = []
			filtro.append( ('id','!=',self.id) )
			if self.partner_id:
				filtro.append( ('partner_id','=',self.partner_id.id) )
			if self.dec_reg_type_document_id:
				filtro.append( ('dec_reg_type_document_id','=',self.dec_reg_type_document_id.id) )
			filtro.append( ('dec_reg_nro_comprobante','=',str(self.dec_reg_nro_comprobante).replace(' ','')) )
			if self.journal_id:
				filtro.append( ('journal_id.type','=', self.journal_id.type) )
			print filtro
			m = self.env['account.move'].search( filtro )
			if len(m) > 0:
				t = str(self.dec_reg_nro_comprobante).replace(' ','')
				raise exceptions.Warning(_("Número de Documento Duplicado ("+t+")."))

	@api.one
	def copy(self,default):
		default['dec_reg_type_document_id']=None
		default['dec_reg_nro_comprobante']=None
		default['dec_mod_type_document_id']=None
		default['dec_mod_nro_comprobante']=None
		default['com_det_date']=None
		default['com_det_amount']=None
		default['com_det_number']=None
		default['com_det_date_maturity']=None
		default['com_det_type_change']=None
		default['com_det_currency']=None
		default['verify_account_invoice_exist']=None
		default['ref']=None
		default['partner_id']=None
		default['dec_mod_fecha']=None
		t= super(account_move, self).copy(default)
		t.dec_reg_type_document_id = None
		t.dec_reg_nro_comprobante = None
		t.dec_mod_type_document_id = None
		t.dec_mod_nro_comprobante = None
		t.com_det_date = None
		t.com_det_amount = None
		t.com_det_number = None
		t.com_det_date_maturity = None
		t.com_det_type_change = None
		t.com_det_currency = None
		t.verify_account_invoice_exist = None
		t.ref =None
		t.partner_id =None	
		t.dec_mod_fecha = None	
		return t
