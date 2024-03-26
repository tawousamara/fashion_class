# -*- coding: utf-8 -*-

{
    'name': "portal Client",
    'description': """Payment Client""",
    'version': '16.0.1.0.0',
    'depends': ['base', 'website','portal'],
    'data': [
        'views/test.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portal-client/static/src/js/client.js',
            'portal-client/static/src/js/payment.js',
            'portal-client/static/src/js/date_search.js',
            'portal-client/static/src/js/generate_pdf.js',
            'portal-client/static/src/js/generate_excel.js',
        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,

}

