# -*- coding: utf-8 -*-

import time
from openerp.osv import osv
from openerp.report import report_sxw


class general_report_account_contable_book(report_sxw.rml_parse):
    _name = 'report.account.contable.book'

    def set_context(self, objects, data, ids, report_type=None):
        print data
        return super(general_report_account_contable_book, self).set_context(objects, data, ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(general_report_account_contable_book, self).__init__(cr, uid, name, context=context)
        
        self.context = context



class report_contable_book(osv.AbstractModel):
    _name = 'report.account_contable_book_it.report_contable_book'
    _inherit = 'report.abstract_report'
    _template = 'account_contable_book_it.report_contable_book'
    _wrapped_report_class = general_report_account_contable_book

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
