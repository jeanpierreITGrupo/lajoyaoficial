# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class pdb_currency_rate_wizard(osv.TransientModel):
	_name='pdb.currency.rate.wizard'
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	
	
	@api.multi
	def do_rebuild(self):
		period_ini = self.period_ini
		
		filtro = []

		self.env.cr.execute("""
		DROP VIEW IF EXISTS pdb_currency_rate;
			CREATE OR REPLACE view pdb_currency_rate as (
				SELECT * 
				FROM get_currency_rates(periodo_num('""" + period_ini.code + """')) 
		)""")

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		Str_csv = self.env['pdb.currency.rate'].search(filtro).mapped(lambda r: self.csv_convert(r,'|'))
		rpta = ""
		#rpta = self.cabezera_csv('|') + "\n"
		for i in Str_csv:
			rpta += i.encode('iso-8859-1','ignore') + "\r\n"

		#code = '0601'
		#periodo = period_ini.code
		#periodo = periodo.split('/')
		#name = periodo[1]+periodo[0]
		user = self.env['res.users'].browse(self.env.uid)

		if user.company_id.id == False:
			raise osv.except_osv('Alerta','El usuario actual no tiene una compañia asignada. Contacte a su administrador.')
		if user.company_id.partner_id.id == False:
			raise osv.except_osv('Alerta','La compañia del usuario no tiene una empresa asignada. Contacte a su administrador.')
		if user.company_id.partner_id.type_number == False:
			raise osv.except_osv('Alerta','La compañia del usuario no tiene un numero de documento. Contacte a su administrador.')

		ruc = user.company_id.partner_id.type_number

		file_name = ruc +'.tc'	


		vals = {
			'output_name': file_name,
			'output_file': base64.encodestring(rpta),		
		}
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}
		

	@api.multi
	def csv_verif_integer(self,data):
		if data:
			return str(data)
		else:
			return ''

	@api.multi
	def csv_verif(self,data):
		if data:
			return data
		else:
			return ''
	@api.multi
	def csv_convert(self,data,separador):
		tmp = self.csv_verif(data.fecha)
		tmp += separador+ self.csv_verif_integer(data.compra)
		tmp += separador+ self.csv_verif_integer(data.venta)
		tmp += separador
		return unicode(tmp)
		
	@api.multi
	def cabezera_csv(self,separador):
		tmp = separador + self.csv_verif("Periodo")
		tmp += separador+ self.csv_verif("Libro")
		tmp += separador+ self.csv_verif("Voucher")
		tmp += separador+ self.csv_verif("Fecha Emision")
		tmp += separador+ self.csv_verif("Fecha Vencimiento")
		tmp += separador+ self.csv_verif("T.D.")
		tmp += separador+ self.csv_verif("Serie")
		tmp += separador+ self.csv_verif("Numero")
		tmp += separador+ self.csv_verif("Tipo de Documento")
		tmp += separador+ self.csv_verif("Num. Documento")
		tmp += separador+ self.csv_verif("Partner")
		tmp += separador+ self.csv_verif("ValorExp")
		tmp += separador+ self.csv_verif("BaseImp")
		tmp += separador+ self.csv_verif("Inafecto")
		tmp += separador+ self.csv_verif("Exonerado")
		tmp += separador+ self.csv_verif("Isc")
		tmp += separador+ self.csv_verif("Igv")
		tmp += separador+ self.csv_verif("Otros")
		tmp += separador+ self.csv_verif("Total")
		tmp += separador+ self.csv_verif("Divisa")
		tmp += separador+ self.csv_verif("Tipo de Cambio")
		tmp += separador+ self.csv_verif("T.D.M")
		tmp += separador+ self.csv_verif("Serie D.")
		tmp += separador+ self.csv_verif("Numero D.")
		tmp += separador
		return unicode(tmp)
		