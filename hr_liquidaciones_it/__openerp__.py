# -*- coding: utf-8 -*-
{
    'name': "Liquidaciones",

    'description': """
        Módulo de liquidaciones
    """,

    'author': "ITGrupo",
    'category': 'hr',
    'version': '0.1',
    'auto_install': False,
    'installable': True,
    'depends': ['hr_nomina_it','hr'],
    'data': ['hr_liquidaciones_view.xml','wizard/hr_liquidaciones_wizard.xml', 'wizard/hr_certificado_trabajo_wizard_view.xml','wizard/reporte_empleado_wizard_view.xml'],
}