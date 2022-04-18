# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
from datetime import datetime
import decimal
import calendar


class hr_uit_historical(models.Model):
	_name = 'hr.uit.historical'
	_rec_name='fiscalyear_id'

	fiscalyear_id = fields.Many2one('account.fiscalyear',u'Año fiscal')
	date_ini      = fields.Date('Fecha incio vigencia')
	date_end      = fields.Date('Fecha fin vigencia')
	amount        = fields.Float('Valor UIT',digist=(12,2))