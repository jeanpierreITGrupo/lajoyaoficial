# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api
from openerp.osv import osv, expression
import pprint 

class hr_five_cat_prob(models.Model):
	_name = 'hr.five.cat.prob'
	_auto =False

	employee_id = fields.Many2one('hr.employee','Trabajador')
	amount      = fields.Float('Monto')

	def init(self, cr):
		tools.drop_view_if_exists(cr, 'hr_five_cat_prob')
		cr.execute("""
			CREATE OR REPLACE view hr_five_cat_prob as (
			select 
			hr_employee.id,
			hr_employee.id as employee_id, 
			case when ((case when hr_employee.children_number>0 then (select monto from hr_parameters where num_tipo = 10001) else 0 end + hr_employee.basica)*14)-((select amount from hr_uit_historical huh
																	  left join account_fiscalyear af on huh.fiscalyear_id = af.id
																	  where af.code = extract(year from current_date)::character varying)*7)>0 then
			((case when hr_employee.children_number>0 then (select monto from hr_parameters where num_tipo = 10001) else 0 end + hr_employee.basica)*14)-((select amount from hr_uit_historical huh
																	     left join account_fiscalyear af on huh.fiscalyear_id = af.id
																	     where af.code = extract(year from current_date)::character varying)*7) else 0 end 
			as amount
			from hr_employee
			where fecha_cese is null)
			""")