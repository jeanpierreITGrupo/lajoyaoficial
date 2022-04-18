# -*- coding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint
import io
from xlsxwriter.workbook import Workbook
import sys
from datetime import datetime
from datetime import timedelta
import os
from dateutil.relativedelta import *
import decimal
import calendar

class hr_tareo_line(models.Model):
	_inherit = 'hr.tareo.line'

	cts_is_payed = fields.Boolean('Sunsidio Descontado en CTS')