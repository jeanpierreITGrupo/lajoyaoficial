# -*- coding: utf-8 -*-
{
    'name': "Parametros IT",

    'description': """
        - Agrega menú Parametros en Almacén
    """,

    'author': "ITGrupo",
    'category': 'mrp',
    'version': '0.1',
    'auto_install': False,
    'installable': True,
    'depends': ['stock'],
    'data': ['security/parameters_security.xml', 'security/ir.model.access.csv', 'warehouse_parameters_view.xml'],
}