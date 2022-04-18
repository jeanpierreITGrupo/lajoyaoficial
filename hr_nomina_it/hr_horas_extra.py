# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api

class hr_horas_extra(models.Model):
	_name = 'hr.horas.extra'
	_rec_name = 'name'
	
	name = fields.Char('Horas Extra', size=20, default=u"Horas Extra")

	"""    MONTO    """
	he_diurnas            = fields.Float('HE DIURNAS', digits=(12,2))
	he_nocturnas          = fields.Float('HE NOCTURNAS', digits=(12,2))
	he_cien_p             = fields.Float('HE 100%', digits=(12,2))
	he_descansos_diurno   = fields.Float('HE DESCANSO DIURNO', digits=(12,2))
	he_descansos_nocturno = fields.Float('HE DESCANSO NOCTURNO', digits=(12,2))
	he_feriados           = fields.Float('HE FERIADO', digits=(12,2))
	he_fer_diur           = fields.Float('HE FERIADO DIURNAS', digits=(12,2))
	he_fer_noct           = fields.Float('HE FERIADO NOCTURNO', digits=(12,2))
		

	def init(self, cr):
		cr.execute('select id from hr_horas_extra')
		ids = cr.fetchall()

		if len(ids) == 0:
			cr.execute("""INSERT INTO hr_horas_extra (name) VALUES ('Horas Extra')""")