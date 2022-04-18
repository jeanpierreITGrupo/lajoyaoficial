# -*- encoding: utf-8 -*-
from openerp.osv import osv

from openerp import models, fields, api

class account_account_analytic_wizard(osv.TransientModel):
	_name='account.account.analytic.wizard'
	
	period_ini =fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end =fields.Many2one('account.period','Periodo Final',required=True)

	@api.onchange('period_ini')
	def _onchange_type_account(self):
		if self.period_ini:
			self.period_end = self.period_ini

	@api.multi
	def do_rebuild(self):

		aaar_obj = self.env['account.account.analytic.rep']

		fechaini_obj = self.period_ini
		fechafin_obj = self.period_end
		
		lstidsaaar = aaar_obj.search([('fecha_ini','>=',fechaini_obj.date_start),('fecha_fin','<=',fechafin_obj.date_stop)])
		
		if (len(lstidsaaar) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
		
		mod_obj = self.env['ir.model.data']

		act_obj = self.env['ir.actions.act_window'] 
		print "llego"
		result = mod_obj.get_object_reference('repaccount_account_analytic_it', 'account_account_analytic_rep_action')
		
		id = result[1]
		print id
		domain_tmp= [('fecha_ini','>=',fechaini_obj.date_start),('fecha_fin','<=',fechafin_obj.date_stop)]
		
		return {
			'domain' : domain_tmp,
			'type': 'ir.actions.act_window',
			'res_model': 'account.account.analytic.rep',
			'view_mode': 'tree',
			'view_type': 'form',
			'res_id': id,
			'views': [(False, 'tree')],
		}






class account_account_analytic_asiento_wizard(osv.TransientModel):
	_name='account.account.analytic.asiento.wizard'

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	fecha = fields.Date('Fecha Asiento',required=True)
	

	@api.multi
	def do_rebuild(self):

		fechaD = self.fecha
		fecha_obj = self.period_ini
		lst_journals = self.env['account.journal'].search([('is_journal_unic','=','True')])

		if (len(lst_journals) == 0) :
			raise osv.except_osv('Alerta','No tiene configurado el Diario para el Asiento Unico.')
		move_obj=self.env['account.account.analytic.rep.contable.unico']
		
		mlra_obj = move_obj.search([('period','=',fecha_obj.id)])
		if (len(mlra_obj) == 0):
			raise osv.except_osv('Alerta','No contiene datos o no esta configurado sus cuentas de amarre.')
		
		periodo = fecha_obj
		#caddel = "delete from account_move where journal_id = "+str(lst_journals)+" and period_id = "+str(fecha_obj.id) + " and ref='" +'Existencias para '+periodo.name + "'"
		#print caddel
		#cr.execute(caddel)
		lineas = []
		for mlra in mlra_obj:
			debit = round(mlra.debe,2)
			credit = round(mlra.haber,2)
			vals = (0,0,{
				'analytic_account_id': False, 
				'tax_code_id': False, 
				'analytic_lines': [], 
				'tax_amount': 0.0, 
				'name': "%s"%('Asiento de Destino Clase 9 para '+periodo.name), 
				'ref': 'Asiento de Destino Clase 9 para '+periodo.name, 
				'debit': debit,
				'credit': credit, 
				'product_id': False, 
				'date_maturity': False, 
				'date': fechaD,
				'product_uom_id': False, 
				'quantity': 0, 
				'partner_id': False, 
				'account_id': int(mlra.cuenta),
				'analytic_line_id': False,
				'nro_comprobante': 'DEST-'+periodo.name,
				'glosa': 'Asiento de Destino Clase 9',
			})
			lineas.append(vals)
			
		move_id = self.env['account.move'].create({
			'company_id': periodo.company_id.id,
			'journal_id': lst_journals.id,
			'period_id': periodo.id,
			'date': fechaD,
			'ref': 'DEST-'+periodo.name, 
			'numopelibro':False,
			'before_numlibro':False,
			'before_numdiario':False,
			'line_id':lineas})			
		return True