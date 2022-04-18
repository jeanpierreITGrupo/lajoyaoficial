# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from openerp.osv import osv
import base64
from zipfile import ZipFile

class resumen_fe(models.TransientModel):
	_name = 'wizard.correlative.it'

	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)
	period_id = fields.Many2one('account.period','Periodo Inicial',required=True)


	@api.onchange('fiscalyear_id')
	def _onchange_fiscalyear(self):
		if self.fiscalyear_id.id:
			peri =self.env['account.period'].search([('fiscalyear_id','=',self.fiscalyear_id.id)])

			return {'domain': {'period_id': [('id', 'in', peri.ids)]}}
		return {}

	@api.onchange('period_id')
	def _onchange_period(self):
		if self.period_id.id:
			fis_id =self.period_id.fiscalyear_id.id
			self.fiscalyear_id = fis_id


	@api.multi
	def do_correlative(self):
		return {
				'type': 'ir.actions.act_window',
				'res_model': 'warning.correlative',
				'view_mode': 'form',
				'view_type': 'form',
				'target': 'new',
			}

	
class resumen_fe(models.TransientModel):
	_name = 'warning.correlative'


	@api.one
	def generate_correlative(self):
		period_id = self.env['wizard.correlative.it'].search([('id','=',self.env.context['active_id'])]).period_id.id
		sql_str = """ create OR REPLACE FUNCTION cambia2() RETURNS INTEGER AS $$
						DECLARE
						v_row RECORD;
						 cont INTEGER:=0;
						BEGIN
						FOR v_row IN (SELECT id, name, vau_anterior FROM account_move where period_id ="""+str(period_id)+"""
and account_move.period_id is not NULL)
						  LOOP
						      UPDATE account_move
						        SET vau_anterior = v_row.name
						        WHERE id = v_row.id;
						        cont:=cont+1;
						  END LOOP;
						RETURN cont;
						END
						$$ LANGUAGE plpgsql;
						SELECT cambia2(); """
		self.env.cr.execute(sql_str)
		dicf=self.env.cr.dictfetchall()