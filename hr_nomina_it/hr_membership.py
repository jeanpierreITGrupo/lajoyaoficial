# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api

class hr_membership_wizard(models.TransientModel):
	_name = 'hr.membership.wizard'

	period_ini = fields.Many2one('account.period','Periodo Origen')
	period_end = fields.Many2one('account.period','Periodo Destino')

	@api.one
	def do_rebuild(self):
		m = self.env['hr.membership.line'].search( [('membership_id','=',self.env.context['membership_id']),('periodo','=',self.period_ini.id)] )
		for i in m:
			data = {
				'membership_id': self.env.context['membership_id'],
				'periodo': self.period_end.id,
				'membership': i.membership.id,
				'tasa_pensiones': i.tasa_pensiones,
				'prima': i.prima,
				'c_variable': i.c_variable,
				'c_mixta': i.c_mixta,
				'rma': i.rma,
			}
			self.env['hr.membership.line'].create(data)

class hr_membership(models.Model):
	_name = 'hr.membership'

	name = fields.Char('Nombre')
	line_id = fields.One2many('hr.membership.line','membership_id','Detalle')

	def init(self, cr):
		cr.execute('select id from hr_membership')
		ids = cr.fetchall()
		if len(ids) == 0:
			cr.execute("""INSERT INTO hr_membership (name) VALUES ('Afiliación')""")

	@api.multi
	def duplicar_periodo(self):
		return {
           'view_type': 'form',
           'view_mode': 'form',
           'res_model': 'hr.membership.wizard',
           'type': 'ir.actions.act_window',
           'target': 'new',
           'context': {'membership_id':self.id},
        }


class hr_membership_line(models.Model):
	_name = 'hr.membership.line'
	_rec_name = 'periodo'

	membership_id = fields.Many2one('hr.membership','Membership')
	periodo = fields.Many2one('account.period', 'Periodo')
	membership = fields.Many2one('hr.table.membership','Afiliación')
	tasa_pensiones = fields.Float('Tasa Fondo Pensiones (%)', digits=(12,2))
	prima = fields.Float('Prima de Seguros (%)', digits=(12,2))
	c_variable = fields.Float('Comisión Variable (%)', digits=(12,2))
	c_mixta = fields.Float('Comisión Mixta (%)', digits=(12,2))
	rma = fields.Float('Remuneración Máxima Asegurable (S/.)', digits=(12,2))

	_order = 'periodo, membership'