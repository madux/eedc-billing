##############################################################################
#    Copyright (C) 2021. All Rights Reserved
#    Enugu Electricity Distribution Company

{
    'name': 'Billing System',
    'version': '14.0',
    'author': "Maduka Chris Sopulu, Paul Ugwu",
    'summary': 'Billing System: To enable the the generation  of bills for individuals',
    'depends': ['base', 'contacts'],
    'description': "Billing System",
    "data": [
            'security\security_view.xml',
            #'security/ir_rule.xml',
            'security\ir.model.access.csv',
            #'data/data.xml',
            'views/res_partner_views.xml',
            'views/hr_employee_inherit_views.xml',
            'views/feeder_views.xml',
            'views/meter_details_views.xml',
            'views/injection_views.xml',
            'views/service_center_views.xml',
            'views/book_feeder_views.xml',
            'views/marketer_views.xml',
            'views/billing_menus_view.xml',

    ],
    'application': True,
    "sequence": 6,
}
