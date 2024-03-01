from odoo import models, fields, api


class FeederCustomerDetails(models.Model):
    _name = 'feeder.customer.details'

    transformer_id = fields.Many2one('feeder.transformer')
    feeder_id = fields.Many2one('feeder.feeder')
    reading_id = fields.Many2one('feeder.reading')
    x_invoice = fields.Integer(string="Invoice ID")
    user_class_id = fields.Many2one('feeder.class', string='Class')
    #user_tarrif = fields.Many2one('feeder.extension', string='New tarrif')
    tarrif_name =  fields.Char()
    tarrif_rate = fields.Integer()
    customer_id = fields.Many2one('res.partner')
    prev_balance = fields.Float()
    last_payment = fields.Float()
    net_arreas = fields.Float()
    prev_read = fields.Float()
    current_read = fields.Float()
    number_class = fields.Integer()
    e_month = fields.Selection( 
        selection=[
            ('Jan', 'January'),
            ('feb', 'February'),
            ('Mar', 'March'),
            ('apr', 'April'),
            ('may', 'May'),
            ('jun', 'June'),
            ('Jul', 'July'),
            ('aug', 'August'),
            ('sep', 'September'),
            ('oct', 'October'),
            ('nov', 'November'),
            ('dec', 'December'), 
        ],
        string='Month',
    )
    e_year = fields.Integer(string='Year')
    consumed = fields.Float(string='Consumed(KWH)')
    adjustment = fields.Float()
    discount = fields.Float()
    amount = fields.Float()
    e_type = fields.Selection(
        selection=[
            ('public_dss', 'Public DSS'),
            ('dt_meter_reading', 'DT Meter Reading'),
            ('md_meter_reading', 'MD Meter Reading'),
            ('md_measured_bulk_reading', 'MD_Measured_Bulk_Reading'),
            ('metered_bulk_reading', 'Metered Bulk Reading'),
        ],
        string='Type',
    )
    vat = fields.Float()
    month_due = fields.Float()
    total_due = fields.Float()


    class FeederTransformer(models.Model):
        _name = 'feeder.transformer'

        name = fields.Char(required=True, string='Transformer Name')
        loc_address = fields.Char(required=True)
        book_ids = fields.One2many('book.feeder', 'transformer_id', string='Books')
        feeder_id = fields.Many2one('feeder.feeder')
        transformer_code = fields.Char('Transformer Code')
        serial_no = fields.Char('Serial No.')
        dss_type = fields.Selection(
            selection=[
                ('private', 'Private'),
                ('public', 'Public'),
                ('bulk', 'Bulk')
            ],
            string='DSS Type'
        )
        dss_make = fields.Char('DSS Make')
        dss_capacity = fields.Integer('DSS Capacity')

    
    class FeederFeeder(models.Model):
        _name = 'feeder.feeder'

        name = fields.Char(required=True, string='Feeder Name')
        code = fields.Char(required=True, string='Feeder code')
        district_id = fields.Many2one('res.district', string='District')
        loc_state = fields.Char(required=True, string='State')
        state = fields.Selection(
            selection=[
                ('active', 'Active'),
                ('suspended', 'Suspended')
            ],
            string='Status'
        )
        injection_id = fields.Many2one('injection.substation')
        created_by = fields.Many2one('res.users', string='Created By')

    
    class FeederReading(models.Model):
        _name = 'feeder.reading'

    class FeederClass(models.Model):
        _name = 'feeder.class'
