# -*- coding: utf-8 -*-

from openerp import models, fields, api


class crossovered_budget_lines(models.Model):
	_inherit = 'crossovered.budget.lines'



	_defaults={
		'date_from': lambda s, cr, uid, c: c['date_from_p'] if 'date_from_p' in c else '',
		'date_to': lambda s, cr, uid, c: c['date_to_p'] if 'date_to_p' in c else '',
	}

	@api.one
	def get_import_real(self):
		self.importe_real = abs(self.practical_amount)


	@api.one
	def get_desviacion(self):
		self.desviacion = self.planned_amount - self.importe_real


	@api.one
	def get_porcentaje_real(self):
		if self.planned_amount == 0:
			self.porcentaje_real="0.00 %"
		else:
			self.porcentaje_real = ("%0.2f"%( (float(self.importe_real) / float(self.planned_amount))*100 )).rjust(8) + ' %'



	@api.one
	def get_porcentaje_real_decimal(self):
		if self.planned_amount == 0:
			self.porcentaje_real_decimal=0
		else:
			self.porcentaje_real_decimal = (float(self.importe_real) / float(self.planned_amount))*100


	importe_real = fields.Float('Importe Real', digits=(12,2) , compute="get_import_real")
	porcentaje_real = fields.Char('Porcentaje', digits=(12,2), compute="get_porcentaje_real")
	porcentaje_real_decimal = fields.Float('Porcentaje', digits=(12,2), compute="get_porcentaje_real_decimal")
	desviacion = fields.Float('Desviación', digits=(12,2), compute="get_desviacion")


class crossovered_budget(models.Model):
	_inherit = 'crossovered.budget'


	period_id = fields.Many2one('account.period','Periodo')


	@api.onchange('period_id')
	def onchange_period_id(self):
		if self.period_id.id:
			self.date_from = self.period_id.date_start
			self.date_to=self.period_id.date_stop



	@api.onchange('date_from')
	def onchange_date_from(self):
		for i in self.crossovered_budget_line:
			i.date_from = self.date_from

	@api.onchange('date_to')
	def onchange_date_to(self):
		for i in self.crossovered_budget_line:
			i.date_to = self.date_to


	def budget_cancel_hecho(self, cr, uid, ids, *args):
		self.write(cr, uid, ids, {
			'state': 'cancel'
		})
		cr.execute("""
		update wkf_instance set state='active'  where id = ( select id from wkf_instance  where res_type = 'crossovered.budget' and res_id = '""" + str(ids[0]) + """' );
		
		update wkf_workitem set state='complete', act_id = ( select id from wkf_activity where wkf_id = (
select id from wkf where name='wkf.crossovered.budget' and osv='crossovered.budget') and name='cancel' )
		where inst_id = ( select id from wkf_instance  where res_type = 'crossovered.budget' and res_id = '""" + str(ids[0]) + """' );
		""")
		return True

	@api.multi
	def do_create_line(self):	

		return {
			'context' : {'date_from_p': self.date_from, 'date_to_p': self.date_to,'active_padre':self.id},
			'type': 'ir.actions.act_window',
			'res_model': 'crossovered.budget.lines.wizard',
			'view_mode': 'form',
			'view_type': 'form',
			'target':'new',
		}



class crossovered_budget_lines_wizard(models.Model):
	
	_name = "crossovered.budget.lines.wizard"

	analytic_account_id= fields.Many2one('account.analytic.account', 'Analytic Account')
	general_budget_id= fields.Many2one('account.budget.post', 'Budgetary Position',required=True)
	planned_amount= fields.Float('Planned Amount', required=True, digits=(12,2) )
	

	@api.multi
	def do_rebuild(self):

		t = self._context['active_padre']

		m = self.env['crossovered.budget'].search([('id','=',t)])[0]
		if m.state != 'draft':
			raise osv.except_osv('Alerta!', "Solo se puede agregar si el Presupuesto esta en borrador.")

		data = {			
			'analytic_account_id':self.analytic_account_id.id,
			'general_budget_id': self.general_budget_id.id,
			'planned_amount': self.planned_amount,
			'crossovered_budget_id': t,
		}


		if 'date_from_p' in self.env.context:
			data['date_from']= self.env.context['date_from_p']

		if 'date_to_p' in self.env.context:
			data['date_to']= self.env.context['date_to_p']

		j = self.env['crossovered.budget.lines'].create(data)
		m.write({'line_id': [(4,j.id)]})

		return True
