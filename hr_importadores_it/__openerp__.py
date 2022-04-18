# -*- coding: utf-8 -*-
{
    'name': "IMPORTADORES RECURSOS HUMANOS IT",

    'description': """
        - Importacion desde un csv:\n
            - tareos\n
            - adelantos
    """,

    'author'      : "ITGrupo",
    'category'    : 'hr',
    'version'     : '0.1',
    'auto_install': False,
    'installable' : True,
    'depends'     : ['hr_nomina_it'],
    'data'        : ['tareo_importador_view.xml',
                     'adelantos_importador_view.xml'],
}