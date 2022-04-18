# -*- encoding: utf-8 -*-
from openerp.osv import osv

from openerp import models, fields, api


class account_expense_rep_wizard(osv.TransientModel):
	_name='account.expense.rep.wizard'
	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	period_end = fields.Many2one('account.period','Periodo Final',required=True)
	type_product = fields.Selection((('t1','Almacenable'),
									('t2','Consumible'),
									('t3','Servicio')									
									),'Tipo Producto')

	@api.onchange('period_ini')
	def _change_periodo_ini(self):
		if self.period_ini:
			self.period_end= self.period_ini

	@api.multi
	def do_rebuild(self):
		fechaini_obj = self.period_ini
		fechafin_obj = self.period_end
		
		move_obj=self.env['account.expense.rep']
		filtro = []
		filtro.append( ('start','>=',fechaini_obj.date_start) )
		filtro.append( ('stop','<=',fechafin_obj.date_stop) )
		
		diccionario = {
			't1': 'Almacenable',
			't2': 'Consumible',
			't3': 'Servicio'
		}

		filtro.append( ('tipoproducto','=','Almacenable') )
		lstidsmove = move_obj.search( filtro )
		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
		


		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		
		result = mod_obj.get_object_reference('repaccount_move_line_it', 'account_expense_rep_action')
		
		id = result and result[1] or False
		return {
			'domain' : filtro,
			'type': 'ir.actions.act_window',
			'res_model': 'account.expense.rep',
			'view_mode': 'tree',
			'view_type': 'form',
			'res_id': id,
			'views': [(False, 'tree')],
		}

class account_expense_rep_asiento_wizard(osv.TransientModel):
	_name='account.expense.rep.asiento.wizard'

	period_ini = fields.Many2one('account.period','Periodo Inicial',required=True)
	fecha = fields.Date('Fecha Asiento',required=True)
	

	@api.multi
	def do_rebuild(self):

		fechaD = self.fecha
		fecha_obj = self.period_ini
		lst_journals = self.env['account.journal'].search([('is_journal_unic','=','True')])

		if (len(lst_journals) == 0) :
			raise osv.except_osv('Alerta','No tiene configurado el Diario para el Asiento Unico.')
		move_obj=self.env['account.expense.asiento.contable.unico']
		
		mlra_obj = move_obj.search([('period','=',fecha_obj.id)])
		if (len(mlra_obj) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
		
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
				'name': "%s"%('Existencias Por Gastos Vinculados para '+periodo.name), 
				'ref': 'Existencias Por Gastos Vinculados para '+periodo.name, 
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
				'nro_comprobante': 'EXIS-G.VIN-'+periodo.name,
				'glosa': 'Asiento de Existencias Por Gastos Vinculados',
			})
			lineas.append(vals)
			
		move_id = self.env['account.move'].create({
			'company_id': periodo.company_id.id,
			'journal_id': lst_journals.id,
			'period_id': periodo.id,
			'date': fechaD,
			'ref': 'EXIS-G.VIN-'+periodo.name, 
			'numopelibro':False,
			'before_numlibro':False,
			'before_numdiario':False,
			'line_id':lineas})		
		return True