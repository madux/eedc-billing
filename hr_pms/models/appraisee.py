from datetime import datetime, timedelta
import time
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo import http
import logging
from lxml import etree

_logger = logging.getLogger(__name__)



class PMS_Appraisee(models.Model):
    _name = "pms.appraisee"
    _description= "Employee appraisee"
    _inherit = "mail.thread"

    @api.constrains('training_section_line_ids')
    def constrain_for_training_section_line_ids(self):
        user_id = self.env.user
        # if the user is administative supervisor => find the lines he has requested
        # and ensure it is not greater than 2
        if self.env.uid not in [self.manager_id.user_id.id, self.administrative_supervisor_id.user_id.id]:
            raise ValidationError('You are not allowed to add training needs')
        if len(self.mapped('training_section_line_ids').\
                   filtered(lambda self: self.env.user.id == self.requester_id.id)) > 2:
            raise ValidationError('Maximum number of training needs added by you must not exceed 2. Please remove the line and save')

    name = fields.Char(
        string="Description Name", 
        required=True,
        size=70
        )
    active = fields.Boolean(
        string="Active", 
        default=True,
        tracking=True
        )
    fold = fields.Boolean(
        string="Fold", 
        default=False
        )
    is_current_user = fields.Boolean(
        default=False, 
        compute="compute_current_user", 
        store=False,
        help="Used to determine what the appraisee sees")

    pms_department_id = fields.Many2one(
        'pms.department', 
        string="PMS Department ID"
        )
    section_id = fields.Many2one(
        'pms.section', 
        string="Section ID",
        )
    submitted_date = fields.Datetime('Submitted Date')
    dummy_kra_section_scale = fields.Integer(
        string="Dummy KRA Section scale",
        help="Used to get the actual kra section scale because it wasnt setup",
        compute="get_kra_section_scale"
        )
            
    employee_id = fields.Many2one(
        'hr.employee', 
        string="Employee"
        )
    employee_number = fields.Char( 
        string="Staff ID",
        related="employee_id.employee_number",
        store=True,
        size=6
        )
    job_title = fields.Char( 
        string="Job title",
        related="employee_id.job_title",
        store=True
        )
    work_unit_id = fields.Many2one(
        'hr.work.unit',
        string="Job title",
        related="employee_id.work_unit_id",
        store=True
        )
    job_id = fields.Many2one(
        'hr.job',
        string="Function", 
        related="employee_id.job_id"
        )
    ps_district_id = fields.Many2one(
        'hr.district',
        string="District", 
        related="employee_id.ps_district_id",
        store=True
        )
    department_id = fields.Many2one(
        'hr.department', 
        string="Department ID"
        )
    reviewer_id = fields.Many2one(
        'hr.employee', 
        string="Reviewer",
        related="employee_id.reviewer_id",
        store=True
        )
    administrative_supervisor_id = fields.Many2one(
        'hr.employee', 
        string="Administrative Supervisor",
        related="employee_id.administrative_supervisor_id",
        store=True
        )
    manager_id = fields.Many2one(
        'hr.employee', 
        string="Functional Manager",
        related="employee_id.parent_id",
        store=True
        )
    approver_ids = fields.Many2many(
        'hr.employee', 
        string="Approvers",
        readonly=True
        )
    appraisee_comment = fields.Text(
        string="Appraisee Comment",
        tracking=True
        )
    appraisee_attachement_ids = fields.Many2many(
        'ir.attachment', 
        'ir_pms_appraisee_attachment_rel',
        'pms_appraisee_attachment_id',
        'attachment_id',
        string="Attachment"
    )
    appraisee_attachement_set = fields.Integer(default=0, required=1) # Added to field to check whether attachment have been updated
    
    
    supervisor_comment = fields.Text(
        string="Supervisor Comment", 
        # tracking=True
        )
    supervisor_attachement_ids = fields.Many2many(
        'ir.attachment', 
        'ir_pms_supervisor_attachment_rel',
        'pms_supervisor_attachment_id',
        'attachment_id',
        string="Attachment"
    )
    supervisor_attachement_set = fields.Integer(default=0, required=1)
    manager_comment = fields.Text(
        string="Manager Comment",
        # tracking=True 
        )
    manager_attachement_ids = fields.Many2many(
        'ir.attachment', 
        'ir_pms_attachment_rel',
        'pms_manager_attachment_id',
        'attachment_id',
        string="Attachment"
    )
    manager_attachement_set = fields.Integer(default=0, required=1)
    reviewer_comment = fields.Text(
        string="Reviewers Comment", 
        # tracking=True,
        )     
        
    reviewer_attachement_ids = fields.Many2many(
        'ir.attachment', 
        'ir_pms_reviewer_attachment_rel',
        'pms_reviewer_attachment_id',
        'attachment_id',
        string="Attachment"
    )
    reviewer_attachement_set = fields.Integer(default=0, required=1)
    appraisee_satisfaction = fields.Selection([
        ('none', 'None'),
        ('fully_agreed', 'Fully Agreed'),
        ('largely_agreed', 'Largely Agreed'),
        ('partially_agreed', 'Partially Agreed'),
        ('largely_disagreed', 'Largely Disagreed'),
        ('totally_disagreed', 'Totally Disagreed'),
        ], string="Perception on PMS", default = "none", 
        tracking=True)
    line_manager_id = fields.Many2one(
        'hr.employee', 
        string="Line Manager"
        )
    
    directed_user_id = fields.Many2one(
        'res.users', 
        string="Appraisal with ?", 
        readonly=True
        )
    kra_section_line_ids = fields.One2many(
        "kra.section.line",
        "kra_section_id",
        string="KRAs"
    )
    lc_section_line_ids = fields.One2many(
        "lc.section.line",
        "lc_section_id",
        string="Leadership Competence"
    )
    fc_section_line_ids = fields.One2many(
        "fc.section.line",
        "fc_section_id",
        string="Functional Competence"
    )
    training_section_line_ids = fields.One2many(
        "training.section.line",
        "training_section_id",
        string="Training section"
    )
    current_assessment_section_line_ids = fields.One2many(
        "current.assessment.section.line",
        "current_assessment_section_id",
        string="Assessment section",
        # default=lambda self: self._get_current_assessment_lines()
    )

    potential_assessment_section_line_ids = fields.One2many(
        'potential.assessment.section.line',
        'potential_section_id',
        string="potential assessment Appraisal"
    )
    qualitycheck_section_line_ids = fields.One2many(
        "qualitycheck.section.line",
        "qualitycheck_section_id",
        string="Quality check section"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('admin_rating', 'Administrative Appraiser'),
        ('functional_rating', 'Functional Appraiser'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Completed'),
        ('signed', 'Signed Off'),
        ('withdraw', 'Withdrawn'), 
        ], string="Status", default = "draft", readonly=True, store=True, tracking=True)

    dummy_state = fields.Selection([
        ('a', 'Draft'),
        ('b', 'Administrative Appraiser'),
        ('c', 'Functional Appraiser'),
        ('d', 'Reviewer'),
        ('e', 'HR to Approve'),
        ('f', 'Completed'),
        ('g', 'Signed Off'),
        ('h', 'Withdrawn'),
        ], string="Dummy Status", readonly=True,compute="_compute_new_state", store=True)
    
    @api.onchange('appraisee_satisfaction')
    def onchange_appraisee_satisfaction(self):
        '''
        This is to trigger the state to notify that employee 
        has completed his perception
        '''
        if self.appraisee_satisfaction != 'none':
            self.update({'state': 'signed'})
        else:
            self.update({'state': 'done'})
    
    @api.depends('state')
    def _compute_new_state(self):
        for rec in self:
            if rec.state == 'draft':
                rec.dummy_state = 'a'
            elif rec.state == 'admin_rating':
                rec.dummy_state = 'b'
            elif rec.state == 'functional_rating':
                rec.dummy_state = 'c'
            elif rec.state == 'reviewer_rating':
                rec.dummy_state = 'd'
            elif rec.state == 'wating_approval':
                rec.dummy_state = 'e'
            elif rec.state == 'done':
                rec.dummy_state = 'f'
            elif rec.state == 'signed':
                rec.dummy_state = 'g'
            else:
                rec.dummy_state = 'h'

    pms_year_id = fields.Many2one(
        'pms.year', string="Period")
    date_from = fields.Date(
        string="Date From", 
        readonly=False, 
        store=True)
    date_end = fields.Date(
        string="Date End", 
        readonly=False,
        store=True
        )
    deadline = fields.Date(
        string="Deadline Date", 
        # compute="get_appraisal_deadline", 
        store=True)
    online_deadline_date = fields.Date(
        string="Appraisee Deadline Date", 
        # compute="get_appraisal_deadline", 
        store=True)

    overall_score = fields.Float(
        string="Overall score", 
        compute="compute_overall_score", 
        store=True)
    
    current_assessment_score = fields.Float(
        string="Current Assessment score", 
        compute="compute_current_assessment_score", 
        store=True)
    potential_assessment_score = fields.Float(
        string="Potential Assessment score", 
        compute="compute_potential_assessment_score", 
        store=True)
    post_normalization_score = fields.Float(
        string="Post normalization score", 
        store=True)

    final_kra_score = fields.Float(
        string='Final KRA Score', 
        store=True,
        compute="compute_final_kra_score"
        )
    
    final_fc_score = fields.Float(
        string='Final FC Score', 
        store=True,
        compute="compute_final_fc_score"
        )
    
    final_lc_score = fields.Float(
        string='Final LC Score', 
        store=True,
        compute="compute_final_lc_score"
        )
    def _get_default_instructions(self):
        ins = self.env.ref('hr_pms.pms_instruction_1').description
        return ins
    
    instruction_html = fields.Text(
        string='Instructions', 
        store=True,
        default=lambda self: self._get_default_instructions(),
        )
    
    # consider removing
    kra_section_weighted_score = fields.Float(
        string='KRA Weight', 
        readonly=True,
        store=True,
        )
    # consider removing
    fc_section_weighted_score = fields.Integer(
        string='Functional Competency Weight', 
        readonly=True,
        store=True,
        )
    # consider removing
    lc_section_weighted_score = fields.Integer(
        string='Leadership Competency Weight', 
        readonly=True,
        store=True,
        )
    # consider removing
    kra_section_avg_scale = fields.Integer(
        string='KRA Scale', 
        readonly=True,
        store=True,
        )
     
    # consider removing
    fc_section_avg_scale = fields.Integer(
        string='Functional Competency Scale', 
        store=True,
        )
    
    reviewer_work_unit = fields.Many2one(
        'hr.work.unit',
        string="Reviewer Unit", 
        related="employee_id.reviewer_id.work_unit_id",
        store=True
        )
    
    # @api.depends()
    # def compute_reviewer_details(self):
    #     reviewer_work_unit=self.employee_id.reviewer_id.hr_work_unit.name
    #     self.reviewer_work_unit = reviewer_work_unit

    #     reviewer_job_id =self.employee_id.reviewer_id.job_id.name
    #     self.reviewer_work_unit = reviewer_job_id

    #     reviewer_job_id =self.employee_id.reviewer_id.job_id.name
    #     self.reviewer_work_unit = reviewer_job_id

    reviewer_job_title = fields.Char(
        string="Reviewer Designation", 
        related="employee_id.reviewer_id.job_title",
        store=True
        )
    reviewer_job_id = fields.Many2one(
        'hr.job',
        string="Reviewer Function",
        related="employee_id.reviewer_id.job_id",
        store=True
        )
    reviewer_district = fields.Many2one(
        'hr.district',
        string="Reviewer District", 
        related="employee_id.reviewer_id.ps_district_id",
        store=True
        )
    reviewer_department = fields.Many2one(
        'hr.department',
        string="Reviewer department", 
        related="employee_id.reviewer_id.department_id",
        store=True
        )
    reviewer_employee_number = fields.Char(
        string="Reviewer Employee Number", 
        related="employee_id.reviewer_id.employee_number",
        store=True
        )
    
    manager_work_unit = fields.Many2one(
        'hr.work.unit',
        string="Manager Unit", 
        related="employee_id.parent_id.work_unit_id",
        store=True
        )
    manager_job_title = fields.Char(
        string="Manager Designation", 
        related="employee_id.parent_id.job_title",
        store=True
        )
    manager_job_id = fields.Many2one(
        'hr.job',
        string="Manager Function", 
        related="employee_id.parent_id.job_id",
        store=True
        )
    manager_district = fields.Many2one(
        'hr.district',
        string="Manager District", 
        related="employee_id.parent_id.ps_district_id",
        store=True
        )
    
    manager_department = fields.Many2one(
        'hr.department',
        string="Manager department", 
        related="employee_id.parent_id.department_id",
        store=True
        )
    manager_employee_number = fields.Char(
        string="Manager Employee Number", 
        related="employee_id.parent_id.employee_number",
        store=True
        )
    supervisor_work_unit = fields.Many2one(
        'hr.work.unit',
        string="Supervisor Unit", 
        related="employee_id.administrative_supervisor_id.work_unit_id",
        store=True
        )
    supervisor_job_title = fields.Char(
        string="Supervisor Designation", 
        related="employee_id.administrative_supervisor_id.job_title",
        store=True
        )
    supervisor_job_id = fields.Many2one(
        'hr.job',
        string="Supervisor Function", 
        related="employee_id.administrative_supervisor_id.job_id",
        store=True
        )
    supervisor_department = fields.Many2one(
        'hr.department',
        string="Supervisor Dept", 
        related="employee_id.administrative_supervisor_id.department_id",
        store=True
        )
    supervisor_district = fields.Many2one(
        'hr.district',
        string="Supervisor District", 
        related="employee_id.administrative_supervisor_id.ps_district_id",
        store=True
        )
    supervisor_employee_number = fields.Char(
        string="Supervisor Employee Number", 
        related="employee_id.administrative_supervisor_id.employee_number",
        store=True
        )
    
    @api.depends('pms_department_id')
    def get_kra_section_scale(self):
        if self.pms_department_id:
            kra_scale = self.pms_department_id.sudo().mapped('section_line_ids').filtered(
                    lambda res: res.type_of_section == "KRA")
            scale = kra_scale[0].section_avg_scale if kra_scale else 4
            self.dummy_kra_section_scale = scale 
        else:
            self.dummy_kra_section_scale = 4
      
    @api.depends('kra_section_line_ids')
    def compute_final_kra_score(self):
        for rec in self:
            if rec.kra_section_line_ids:
                kra_total = sum([
                    weight.weighted_score for weight in rec.mapped('kra_section_line_ids')
                    ])
                rec.final_kra_score = kra_total
            else:
                rec.final_kra_score = 0

    @api.depends('fc_section_line_ids')
    def compute_final_fc_score(self):
        for rec in self:
            if rec.fc_section_line_ids:
                fc_total = sum([
                    weight.weighted_score for weight in rec.mapped('fc_section_line_ids')
                    ])
                rec.final_fc_score = fc_total
            else:
                rec.final_fc_score = 0

    @api.depends('lc_section_line_ids')
    def compute_final_lc_score(self):
        for rec in self:
            if rec.lc_section_line_ids:
                fc_total = sum([
                    weight.weighted_score for weight in rec.mapped('lc_section_line_ids')
                    ])
                rec.final_lc_score = fc_total 
            else:
                rec.final_lc_score = 0

    @api.depends(
            'final_kra_score',
            'final_lc_score',
            'final_fc_score'
            ) 
    def compute_overall_score(self):
        for rec in self:
            if rec.final_kra_score and rec.final_lc_score and rec.final_fc_score:
                kra_section_weighted_score = rec.pms_department_id.hr_category_id.kra_weighted_score 
                fc_section_weighted_score = rec.pms_department_id.hr_category_id.fc_weighted_score
                lc_section_weighted_score = rec.pms_department_id.hr_category_id.lc_weighted_score 

                # rec.section_id.weighted_score
                # e.g 35 % * kra_final + 60% * lc_final * 15% + fc_final * 45%
                # e.g 35 % * kra_final + 0.60% * lc_final * 0.15% + fc_final * 0.45

                rec.overall_score = (kra_section_weighted_score / 100) * rec.final_kra_score + \
                (fc_section_weighted_score/ 100) * rec.final_fc_score + \
                (lc_section_weighted_score/ 100) * rec.final_lc_score
            else:
                rec.overall_score = 0
    
    @api.depends(
            'current_assessment_section_line_ids',
            )
    def compute_current_assessment_score(self):
        'get the lines for appraisers and compute'
        ar_rating = 0
        fa_rating = 0
        fr_rating = 0
        ar = self.mapped('current_assessment_section_line_ids').filtered(
            lambda s: s.state == 'admin_rating'
        )
        fa = self.mapped('current_assessment_section_line_ids').filtered(
            lambda s: s.state == 'functional_rating'
        )
        fr = self.mapped('current_assessment_section_line_ids').filtered(
            lambda s: s.state == 'reviewer_rating'
        )
        if ar:
            ar_rating = ar[0].administrative_supervisor_rating or 0 # e.g 2
        if fa:
            fa_rating = fa[0].functional_supervisor_rating or 0 # e.g 2
        if fr:
            fr_rating = fr[0].reviewer_rating or 0
        # fr_rt = 30 if self.employee_id.administrative_supervisor_id else 60
        if self.employee_id.administrative_supervisor_id:
            ar_rating = ar_rating * 30
            fa_rating = fa_rating * 30
        else:
            ar_rating = ar_rating * 0
            fa_rating = fa_rating * 60
        weightage = (ar_rating) + (fa_rating) + (fr_rating * 40)
        # raise ValidationError(f"weightage =={weightage} fr_rt ==>{fr_rt} --- ar {ar_rating}--- fr_rating {fr_rating} fa_rating ==>{fa_rating}")
        self.current_assessment_score = weightage / 4

    @api.depends(
        'potential_assessment_section_line_ids',
        )
    def compute_potential_assessment_score(self):
        'get the lines for appraisers and compute'
        ar_rating = 0
        fa_rating = 0
        fr_rating = 0
        ar = self.mapped('potential_assessment_section_line_ids').filtered(
            lambda s: s.state == 'admin_rating'
        )
        fa = self.mapped('potential_assessment_section_line_ids').filtered(
            lambda s: s.state == 'functional_rating'
        )
        fr = self.mapped('potential_assessment_section_line_ids').filtered(
            lambda s: s.state == 'reviewer_rating'
        )
        if ar:
            ar_rating = ar[0].administrative_supervisor_rating or 0
        if fa:
            fa_rating = fa[0].functional_supervisor_rating or 0
        if fr:
            fr_rating = fr[0].reviewer_rating or 0
        if self.employee_id.administrative_supervisor_id:
            ar_rating = ar_rating * 30
            fa_rating = fa_rating * 30
        else:
            ar_rating = ar_rating * 0
            fa_rating = fa_rating * 60
        weightage = (ar_rating) + (fa_rating) + (fr_rating * 40)
        self.potential_assessment_score = weightage / 4

    def check_kra_section_lines(self):
        # if the employee has administrative reviewer, 
        # system should validate to see if they have rated
        if self.state == "admin_rating":
            if self.mapped('kra_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating on KRA section is at least 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('kra_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating on KRA section is at least 1"
                ) 
            
    def check_fc_section_lines(self):
        if self.state == "admin_rating":
            if self.mapped('fc_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating on functional competency section is at least 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('fc_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating on functional competency line is at least 1"
                )

        elif self.state == "reviewer_rating":
            if self.mapped('fc_section_line_ids').filtered(
                lambda line: line.reviewer_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager rating's on functional competency line is at least rated 1"
                ) 
            
    def check_lc_section_lines(self):
        if self.state == "admin_rating":
            if self.mapped('lc_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating at leadership competency is at least 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('lc_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating at leadership competency is at least 1"
                )

        elif self.state == "reviewer_rating":
            if self.mapped('lc_section_line_ids').filtered(
                lambda line: line.reviewer_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all reviewer's rating at leadership competency is at least 1"
                ) 
    
    def check_current_potential_assessment_section_lines(self):
        if self.state == "admin_rating":
            if self.mapped('current_assessment_section_line_ids').filtered(
                lambda line: line.name == "Administrative Appraiser" and line.assessment_type == False):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating at current assessment section is at least Ordinary"
                )
            if self.mapped('potential_assessment_section_line_ids').filtered(
                lambda line: line.name == "Administrative Appraiser" and line.assessment_type == False):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating at potential assessment section is at least Low potential"
                )
            
        elif self.state == "functional_rating":
            if self.mapped('current_assessment_section_line_ids').filtered(
                lambda line: line.name == "Functional Appraiser" and line.assessment_type == False):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating at current assessment section is at least Ordinary"
                )
            if self.mapped('potential_assessment_section_line_ids').filtered(
                lambda line: line.name == "Functional Appraiser" and line.assessment_type == False):
                raise ValidationError(
                    "Ops! Please ensure all  functional manager's rating at potential assessment section is at least Low potential"
                )

        elif self.state == "reviewer_rating":
            if self.mapped('current_assessment_section_line_ids').filtered(
                lambda line: line.name == "Functional Reviewer" and line.assessment_type == False):
                raise ValidationError(
                    "Ops! Please ensure all reviewer's rating at current assessment section is at least "
                ) 
            if self.mapped('potential_assessment_section_line_ids').filtered(
                lambda line: line.name == "Functional Reviewer" and line.assessment_type == False):
                raise ValidationError(
                    "Ops! Please ensure all reviewer's rating at potential assessment section is at least Low potential"
                )
            
    # def check_potential_assessment_section_lines(self):
    #     if self.state == "admin_rating":
    #         if self.mapped('potential_assessment_section_line_ids').filtered(
    #             lambda line: line.administrative_supervisor_rating < 1):
    #             raise ValidationError(
    #                 "Ops! Please ensure all administrative supervisor's rating on potential assessment section is at least 1"
    #             )
    #         if self.mapped('potential_assessment_section_line_ids').filtered(
    #             lambda line: line.administrative_supervisor_rating < 1):
    #             raise ValidationError(
    #                 "Ops! Please ensure all administrative supervisor's rating on potential assessment section is at least 1"
    #             )
    #     elif self.state == "functional_rating":
    #         if self.mapped('potential_assessment_section_line_ids').filtered(
    #             lambda line: line.functional_supervisor_rating < 1):
    #             raise ValidationError(
    #                 "Ops! Please ensure all functional manager's rating on potential assessment section is at least 1"
    #             )

    #     elif self.state == "reviewer_rating":
    #         if self.mapped('potential_assessment_section_line_ids').filtered(
    #             lambda line: line.reviewer_rating < 1):
    #             raise ValidationError(
    #                 "Ops! Please ensure all reviewer's rating on potential assessment section is at least 1"
    #             ) 
        
    def _get_group_users(self):
        group_obj = self.env['res.groups']
        hr_administrator = self.env.ref('hr.group_hr_manager').id
        pms_manager = self.env.ref('hr_pms.group_pms_manager_id').id
        pms_officer = self.env.ref('hr_pms.group_pms_officer_id').id
        hr_administrator_user = group_obj.browse([hr_administrator])
        pms_manager_user = group_obj.browse([pms_manager])
        pms_officer_user = group_obj.browse([pms_officer])

        hr_admin = hr_administrator_user.mapped('users') if hr_administrator_user else False
        pms_mgr = pms_manager_user.mapped('users') if pms_manager_user else False
        pms_off = pms_officer_user.mapped('users') if pms_officer_user else False
        return hr_admin, pms_mgr, pms_off
    
    def submit_mail_notification(self): 
        subject = "Appraisal Notification"
        department_manager = self.employee_id.parent_id or self.employee_id.parent_id
        supervisor = self.employee_id.administrative_supervisor_id
        reviewer_id = self.employee_id.reviewer_id
        hr_admin, pms_mgr, pms_off = self._get_group_users()
        hr_emails = [rec.login for rec in hr_admin]
        pms_mgr_emails = [rec.login for rec in pms_mgr]
        pms_off_emails = [rec.login for rec in hr_admin]
        hr_logins = hr_emails + pms_mgr_emails + pms_off_emails
        if not hr_logins:
            raise ValidationError('Please ensure there is a user with HR addmin settings')
        if self.state in ['draft']:
            if department_manager and department_manager.work_email:
                msg = """Dear {}, <br/>
                I wish to notify you that my appraisal has been submitted to you for rating(s) \
                <br/>Kindly {} to proceed with the ratings <br/>\
                Yours Faithfully<br/>{}<br/>Department: ({})""".format(
                    department_manager.name,
                    self.get_url(self.id, self._name),
                    self.env.user.name,
                    self.employee_id.department_id.name,
                    )
                email_to = department_manager.work_email
                email_cc = [
                    supervisor.work_email, 
                    reviewer_id.work_email,
                ]
            else:
                raise ValidationError(
                    'Please ensure that employee / department \
                    manager has an email address')
        elif self.state in ['rating']:
            msg = """HR, <br/>
                I wish to notify you that an appraisal for {} \
                has been submitted for HR processing\
                <br/>Kindly {} to review the appraisal<br/>\
                Yours Faithfully<br/>{}<br/>""".format(
                    self.employee_id.name,
                    self.get_url(self.id, self._name),
                    self.env.user.name,
                    )
            email_to = ','.join(hr_logins)
            email_cc = [
                    supervisor.work_email, 
                    reviewer_id.work_email,
                ]
        elif self.state in ['wating_approval']:
            msg = """HR, <br/>
                I wish to notify you that an appraisal for {} has been completed.\
                <br/>Kindly {} to review the appraisal. <br/> \
                For further Inquiry, contact HR Department<br/>\
                Yours Faithfully<br/>{}<br/>""".format(
                    self.employee_id.name,
                    self.get_url(self.id, self._name),
                    self.env.user.name,
                    )
            email_to = self.employee_id.work_email
            email_cc = [
                    supervisor.work_email, 
                    reviewer_id.work_email,
                    department_manager.work_email
                ]
        else:
            msg = "-"
            email_to = department_manager.work_email
            email_cc = [
                    supervisor.work_email, 
                    reviewer_id.work_email,
                ]
        self.action_notify(
            subject, 
            msg, 
            email_to, 
            email_cc)
        
    def get_email_from(self):
        email_from = ""
        if self.state == "admin_rating":
            email_from = self.administrative_supervisor_id.work_email
        if self.state == "functional_rating":
            email_from = self.manager_id.work_email
        if self.state == "reviewer_rating":
            email_from = self.manager_id.work_email or self.administrative_supervisor_id.work_email
        return email_from
        
    def action_notify(self, subject, msg, email_to, email_cc):
        sender_email_from = self.env.user.email
        email_from = sender_email_from or self.get_email_from()
        if email_to and email_from:
            email_ccs = list(filter(bool, email_cc))
            reciepients = (','.join(items for items in email_ccs)) if email_ccs else False
            mail_data = {
                    'email_from': email_from,
                    'subject': subject,
                    'email_to': email_to,
                    'reply_to': email_from,
                    'email_cc': reciepients,
                    'body_html': msg,
                    'state': 'sent'
                }
            mail_id = self.env['mail.mail'].sudo().create(mail_data)
            # self.env['mail.mail'].sudo().send(mail_id)
            # self.message_post(body=msg)
    
    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web'
        # base_url += '/web#id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>. ".format(base_url)

    def action_send_reminder(self):
        msg = """Dear, <br/> 
            I wish to remind you of the appraisal currently on your desk. <br/> \
            Please kindly review and do the needful.<br/> \
            Yours Faithfully<br/>{}<br/>""".format(
                self.env.user.name,
                self.department_id.name,
                )
        subject = "Appraisal Reminder"
        email_to = self.employee_id.work_email or self.administrative_supervisor_id.work_email or self.manager_id.work_email if self.state in ['draft', 'done', 'reviewer_rating'] else \
            self.administrative_supervisor_id.work_email if self.state == "admin_rating" else \
            self.manager_id.work_email if self.state == "functional_rating" else self.reviewer_id.work_email if self.state == "reviewer_rating" else self.employee_id.work_email
        email_cc = [self.employee_id.work_email]
        self.action_notify(subject, msg, email_to, email_cc)

    def mass_send_reminder(self):
        rec_ids = self.env.context.get('active_ids', [])
        for record in rec_ids:
            rec = self.env['pms.appraisee'].browse([record])
            msg = """Dear {}, <br/> 
                I wish to remind you of the appraisal currently on your desk. <br/> \
                Please kindly rate and submit before the submission deadline.
                You can choose to ignore if necessary process has been done. <br/> \
                Regards<br/>
                HR: {}<br/>
                """.format(
                    rec.employee_id.name,
                    rec.write_uid.company_id.name,
                    )
            subject = "Appraisal Reminder"
            email_to = rec.employee_id.work_email or rec.administrative_supervisor_id.work_email or rec.manager_id.work_email if rec.state in ['draft', 'done', 'reviewer_rating'] else \
                rec.administrative_supervisor_id.work_email if self.state == "admin_rating" else \
                rec.manager_id.work_email if rec.state == "functional_rating" else rec.reviewer_id.work_email if rec.state == "reviewer_rating" else rec.employee_id.work_email
            email_cc = [rec.employee_id.work_email]
            rec.action_notify(subject, msg, email_to, email_cc)
    
    def send_mail_notification(self, msg):
        subject = "Appraisal Notification"
        administrative_supervisor = self.employee_id.administrative_supervisor_id
        reviewer_id = self.employee_id.reviewer_id
        # doing this to avoid making calls that will impact optimization
        department_manager = self.employee_id.parent_id
        if self.state == "draft":
            email_to = administrative_supervisor.work_email if self.administrative_supervisor_id.work_email else department_manager.work_email
            email_cc = [
            department_manager.work_email,
            reviewer_id.work_email, 
            administrative_supervisor.work_email,
        ]
        elif self.state == "admin_rating":
            email_to = department_manager.work_email
            email_cc = [
                department_manager.work_email,
                self.employee_id.work_email
                ]
        elif self.state == "functional_rating":
            email_to = reviewer_id.work_email
            email_cc = [
                department_manager.work_email,
                self.employee_id.work_email,
                administrative_supervisor.work_email,
                ]
        elif self.state == "reviewer_rating":
            email_to = self.employee_id.work_email,
            email_cc = [
                department_manager.work_email,
                administrative_supervisor.work_email,
                ]
        else:
            email_to = department_manager.work_email,
            email_cc = [
                department_manager.work_email,
                administrative_supervisor.work_email,
                ]
        self.action_notify(subject, msg, email_to, email_cc)

    def validate_weightage(self):
        kra_line = self.sudo().pms_department_id.mapped('section_line_ids').filtered(
                    lambda res: res.type_of_section == "KRA")
        if kra_line:
            max_line_number = kra_line[0].max_line_number
            min_line_number = kra_line[0].min_line_number
            min_limit = 5
            max_limit = 7
            if max_line_number > 0:
                max_limit = max_line_number
                min_limit = min_line_number
            else:
                category_kra_line = self.sudo().pms_department_id.hr_category_id.sudo().mapped('section_ids').filtered(
                    lambda res: res.type_of_section == "KRA")
                min_category_line_number = category_kra_line[0].min_line_number if category_kra_line and category_kra_line[0].max_line_number > 0 else min_limit
                max_category_line_number = category_kra_line[0].max_line_number if category_kra_line and category_kra_line[0].max_line_number > 0 else max_limit
                max_limit = max_category_line_number
                min_limit = min_category_line_number
            if len(self.kra_section_line_ids.ids) not in range(min_limit, max_limit + 1): # not in [5, 6, limit]:
                raise ValidationError("""Please ensure the number of KRA / Achievement section is within the range of {} to {} line(s)""".format(int(min_limit), int(max_limit)))
        sum_weightage = sum([weight.appraisee_weightage for weight in self.mapped('kra_section_line_ids')])
        if sum_weightage != 100:
            value_diff = 100 - sum_weightage 
            needed_value_msg = f'''You need to add {value_diff}%''' if value_diff > 0 else f'''You need to deduct {abs(value_diff)}%'''
            raise ValidationError(
                f"""Please ensure the sum of KRA weight by functional Appraiser is equal to 100 %.\n {needed_value_msg} weightage to complete it"""
                )
        
    def validate_deadline(self):
        appraisee_deadline = self.sudo().pms_department_id.hr_category_id.online_deadline_date
        if appraisee_deadline and fields.Date.today() > appraisee_deadline:
            raise ValidationError('Your deadline for submission has exceeded !!!')
        if self.deadline and fields.Date.today() > self.deadline:
            raise ValidationError('You have exceeded deadline for the submission of your appraisal')
        
    def button_submit(self):
        # send notification
        self.validate_deadline()
        self.validate_weightage()
        admin_or_functional_user = self.administrative_supervisor_id.name or self.manager_id.name
        msg = """Dear {}, <br/> 
        I wish to notify you that an appraisal for {} \
        has been submitted for ratings.\
        <br/>Kindly {} to review <br/>\
        Yours Faithfully<br/>{}<br/>HR Department ({})""".format(
            admin_or_functional_user,
            self.employee_id.name,
            self.get_url(self.department_id.id, self._name),
            self.env.user.name,
            self.department_id.name,
            )
        self.send_mail_notification(msg)
        
        if self.employee_id.administrative_supervisor_id:
            self.write({
                'state': 'admin_rating',
                'submitted_date': fields.Date.today(),
                'administrative_supervisor_id': self.employee_id.administrative_supervisor_id.id,
            })
        else:
            self.write({
                'state': 'functional_rating',
                'submitted_date': fields.Date.today(),
                'manager_id': self.employee_id.parent_id.id,
            })
            
    def button_admin_supervisor_rating(self): 
        msg = """Dear {}, <br/> 
        I wish to notify you that an appraisal for {} \
        has been submitted for functional manager's ratings.\
        <br/>Kindly {} to review <br/>\
        Yours Faithfully<br/>{}<br/>HR Department ({})""".format(
            self.employee_id.parent_id.name,
            self.employee_id.name,
            self.get_url(self.department_id.id, self._name),
            self.env.user.name,
            self.administrative_supervisor_id.department_id.name,
            )
        if not self.employee_id.parent_id:
            raise ValidationError(
                'Ops ! please ensure that a manager is assigned to the employee'
                )
        if self.employee_id.administrative_supervisor_id and self.env.user.id != self.administrative_supervisor_id.user_id.id:
            raise ValidationError(
                "Ops ! You are not entitled to submit this rating because you are not the employee's administrative supervisor"
                )
        self.check_kra_section_lines()
        self.check_fc_section_lines()
        self.check_lc_section_lines()
        self.check_current_potential_assessment_section_lines()
        # self.check_current_assessment_section_lines()
        # self.check_potential_assessment_section_lines()
        self.send_mail_notification(msg)
        self.write({
                'state': 'functional_rating',
                'manager_id': self.employee_id.parent_id.id,
            })
        # if self.supervisor_attachement_ids:
        #         self.supervisor_attachement_ids.write({'res_model': self._name, 'res_id': self.id})
        
    def button_functional_manager_rating(self):
        if not self.employee_id.reviewer_id:
            raise ValidationError(
                "Ops ! please ensure that a reviewer is assigned to the employee"
                )
        sum_weightage = sum([weight.weightage for weight in self.mapped('kra_section_line_ids')])
        if sum_weightage != 100:
            value_diff = 100 - sum_weightage 
            needed_value_msg = f'''You need to add {value_diff}%''' if value_diff > 0 else f'''You need to deduct {abs(value_diff)}%'''
            raise ValidationError(
                f"""Please ensure the sum of KRA weight by Appraisee is equal to 100 %.\n {needed_value_msg} weightage to complete it"""
                )
        
        if self.employee_id.parent_id and self.env.user.id != self.employee_id.parent_id.user_id.id:
            raise ValidationError(
                "Ops ! You are not entitled to submit this rating because you are not the employee's functional manager"
                )
        self.check_kra_section_lines()
        self.check_fc_section_lines()
        self.check_lc_section_lines()
        self.check_current_potential_assessment_section_lines()
        # self.check_current_assessment_section_lines()
        # self.check_potential_assessment_section_lines()
        msg = """Dear {}, <br/> 
        I wish to notify you that an appraisal for {} \
        has been submitted for reviewer's ratings.\
        <br/>Kindly {} to review <br/>\
        Yours Faithfully<br/>{}<br/>HR Department ({})""".format(
            self.employee_id.parent_id.name,
            self.employee_id.name,
            self.get_url(self.department_id.id, self._name),
            self.env.user.name,
            self.manager_id.department_id.name,
            )
        self.send_mail_notification(msg)
        self.write({
                'state': 'reviewer_rating',
                'reviewer_id': self.employee_id.reviewer_id.id,
            })
        # if self.manager_attachement_ids:
        #         self.manager_attachement_ids.write({'res_model': self._name, 'res_id': self.id})
    
    def button_reviewer_manager_rating(self):
        if self.employee_id.reviewer_id and self.env.user.id != self.employee_id.reviewer_id.user_id.id:
            raise ValidationError(
                "Ops ! You are not entitled to submit this rating because you are not the employee's reviewing manager"
                )
        self.check_fc_section_lines()
        self.check_lc_section_lines()
        self.check_current_potential_assessment_section_lines()
        msg = """Dear {}, <br/> 
        I wish to notify you that your appraisal has been reviewed successfully.\
        Yours Faithfully<br/>{}<br/>HR Department ({})""".format(
            self.employee_id.name,
            self.env.user.name,
            self.reviewer_id.department_id.name,
            )
        self.send_mail_notification(msg)
        self.write({
                'state': 'done',
            })
        # if self.reviewer_attachement_ids:
        #         self.reviewer_attachement_ids.write({'res_model': self._name, 'res_id': self.id})
        
    def _check_lines_if_appraisers_have_rated(self):
        kra_section_line_ids = self.mapped('kra_section_line_ids').filtered(lambda s: s.administrative_supervisor_rating > 0 or s.functional_supervisor_rating > 0)
        if self.employee_id and self.env.user.id != self.employee_id.user_id.id:
            raise ValidationError(
                "Ops ! You are not entitled to withdraw the employee's appraisal"
                )
        if kra_section_line_ids:
            raise ValidationError('You cannot withdraw this document because appraisers has started ratings on it')
        
    
    def button_withdraw(self):
        self._check_lines_if_appraisers_have_rated()
        self.write({
                'state':'withdraw',
            })
        
    def button_set_to_draft(self):
        self.write({
                'state':'draft',
            })
        
    
    # @api.model
    # def fields_view_get(self, view_id='hr_pms.view_hr_pms_appraisee_form', view_type='form', toolbar=False, submenu=False):
    #     res = super(PMS_Appraisee, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                 submenu = submenu)
    #     doc = etree.XML(res['arch'])
    #     active_id = self.env.context.get('active_id', False)
    #     if self.env.uid == self.administrative_supervisor_id.user_id.id:
    #         raise ValidationError(f"""{self.env.uid} {self.administrative_supervisor_id.user_id.id} {active_id}""")
    #     else:
    #         raise ValidationError(f"""fff {self.env.uid} {self.env.context.get('administrative_supervisor_id')}  {active_id}""")

    #         # if self.env.user.has_group('hr_pms.group_unmc_admin') == False or self.env.user.has_group('hr_pms.group_unmc_doctor') == False:
    #         for node in doc.xpath("//button[@name='button_admin_supervisor_rating']"):
    #             node.set('modifiers', '{"invisible": false}')
    #     #     for node in doc.xpath("//field[@name='test_type_id']"):
    #     #         node.set('modifiers', '{"readonly": true}')
                
    #     #     for node in doc.xpath("//field[@name='patient_id']"):
    #     #         node.set('modifiers', '{"readonly": true}')
                
    #     #     for node in doc.xpath("//field[@name='date_requested']"):
    #     #         node.set('modifiers', '{"readonly": true}')
                
    #     #     for node in doc.xpath("//field[@name='hospital']"):
    #     #         node.set('modifiers', '{"readonly": true}')
                
    #     #     for node in doc.xpath("//field[@name='patient']"):
    #     #         node.set('modifiers', '{"readonly": true}')
    #     #     for node in doc.xpath("//field[@name='test_type']"):
    #     #         node.set('modifiers', '{"readonly": true}')
                
    #     #     for node in doc.xpath("//field[@name='requested_by']"):
    #     #         node.set('modifiers', '{"readonly": true}')
    #     # elif not (self.env.user.has_group('hr_pms.group_unmc_lab_two') or self.env.user.has_group('hr_pms.group_unmc_admin')):
    #     #     for node in doc.xpath("//field[@name='result']"):
    #     #         node.set('modifiers', '{"readonly": true}')
    #     #     for node in doc.xpath("//field[@name='recorded_by']"):
    #     #         node.set('modifiers', '{"readonly": true}')
                
    #     #     for node in doc.xpath("//field[@name='notes']"):
    #     #         node.set('modifiers', '{"readonly": true}')
                
    #     #     for node in doc.xpath("//field[@name='date_of_testing']"):
    #     #         node.set('modifiers', '{"readonly": true}')
    #     res['arch'] = etree.tostring(doc)
    #     return res
    
    # @api.model
    # def create(self, vals):
    #     templates = super(PMS_Appraisee,self).create(vals)
    #     for template in templates:
    #         if template.appraisee_attachement_ids:
    #             template.appraisee_attachement_ids.write({'res_model': self._name, 'res_id': template.id})
    #         if template.supervisor_attachement_ids:
    #             template.supervisor_attachement_ids.write({'res_model': self._name, 'res_id': template.id})
    #         if template.manager_attachement_ids:
    #             template.manager_attachement_ids.write({'res_model': self._name, 'res_id': template.id})
    #         if template.reviewer_attachement_ids:
    #             template.reviewer_attachement_ids.write({'res_model': self._name, 'res_id': template.id})
    #     return templates
    
    
    def validate_reviewer_commenter(self, vals):
        old_comment = vals.get('reviewer_comment')
        if old_comment and self.state == 'reviewer_rating':
            if self.employee_id.reviewer_id and self.env.user.id != self.employee_id.reviewer_id.user_id.id:
                raise UserError("Ops ! You are not entitled to add a review comment because you are not the employee's reviewer")
        
    def write(self, vals):
        
        self.validate_reviewer_commenter(vals)
        res = super().write(vals)
        for template in self:
            if template.appraisee_attachement_ids and template.appraisee_attachement_set == 0:
                template.appraisee_attachement_ids.write({'res_model': self._name, 'res_id': template.id})
                template.appraisee_attachement_set = 1

            if template.supervisor_attachement_ids and template.supervisor_attachement_set == 0:
                template.supervisor_attachement_ids.write({'res_model': self._name, 'res_id': template.id})
                template.supervisor_attachement_set = 1

            if template.manager_attachement_ids and template.manager_attachement_set == 0:
                template.manager_attachement_ids.write({'res_model': self._name, 'res_id': template.id})
                template.manager_attachement_set = 1

            if template.reviewer_attachement_ids and template.reviewer_attachement_set == 0:
                template.reviewer_attachement_ids.write({'res_model': self._name, 'res_id': template.id})
                template.reviewer_attachement_set = 1
            # if is_not_reviewer:
            #     template.write({'reviewer_comment': old_comment})
        return res
    
    def _get_non_draft_pms(self):
        pms = self.env['pms.appraisee'].search_count([('state', '!=', 'draft')])
        return int(pms) if pms else 0
    
    def _get_overdue_pms(self):
        submitted_pms = self.env['pms.appraisee'].search(
            [('state', 'in', ['admin_rating', 'functional_rating'])])
        total_overdue = 0
        if submitted_pms:
            # dd = (submitted_pms[0].submitted_date - submitted_pms[0].create_date).days
            # raise ValidationError(dd)
            total_overdue = len([rec for rec in submitted_pms if (rec.submitted_date - rec.create_date).days > 2])
        return total_overdue
    
    def _get_completed_pms(self):
        pms = self.env['pms.appraisee'].search_count([('state', 'in', ['done', 'signed'])])
        return int(pms) if pms else 0
    
    def _get_perception_pms(self, perception): 
        pms = self.env['pms.appraisee'].search_count([('appraisee_satisfaction', 'in', perception)])
        return int(pms) if pms else 0
    
    def _get_reviewer_pms(self):
        pms = self.env['pms.appraisee'].search_count([('state', '=', 'reviewer_rating')])
        return int(pms) if pms else 0
    
    def _getpms_not_generated(self):
        pms = self.env['pms.appraisee'].search([])
        employees = self.env['hr.employee'].search([]).ids
        pms_employee_ids = [rec.employee_id.id for rec in pms]
        number_of_intersections = set(pms_employee_ids).intersection(employees)
        return len(number_of_intersections) if number_of_intersections else 0
    
    @api.model
    def get_dashboard_details(self):
        return {
            '_get_non_draft_pms': self._get_non_draft_pms(),
            '_get_overdue_pms': self._get_overdue_pms(),
            '_get_completed_pms': self._get_completed_pms(),
            '_get_perception_agreed_pms': self._get_perception_pms(['fully_agreed','largely_agreed','partially_agreed']),
            '_get_perception_disagreed_pms': self._get_perception_pms(['totally_disagreed', 'largely_disagreed']),
            '_get_reviewer_pms': self._get_reviewer_pms(),
            '_getpms_not_generated': self._getpms_not_generated(),
        }
    
    def overdue_pms(self):
        submitted_pms = self.env['pms.appraisee'].search(
            [('state', 'in', ['admin_rating', 'functional_rating'])])
        total_overdue_ids = [0]
        if submitted_pms:
            total_overdue_ids = [rec.id for rec in submitted_pms if (rec.submitted_date - rec.create_date).days > 2]
        return total_overdue_ids
    
    def compute_current_user(self):
        for rec in self:
            if rec.employee_id.user_id.id == self.env.user.id and rec.state not in ['draft','done', 'signed']:
                rec.is_current_user = True
            else:
                rec.is_current_user = False
    reason_back = fields.Text(string='Return Reasons', tracking=True)
    is_functional_appraiser = fields.Boolean(string='Is functional appraiser', compute="compute_functional_appraiser")

    def compute_functional_appraiser(self):
        if self.manager_id and self.manager_id.user_id.id == self.env.user.id:
            self.is_functional_appraiser = True 
        else:
            self.is_functional_appraiser = False

    def return_appraisal(self):
        return {
              'name': 'Reason for Return',
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'pms.back',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': {
                  'default_record_id': self.id,
                  'default_date': fields.Datetime.now(),
                  'default_direct_employee_id': self.employee_id.id,
                  'default_resp':self.env.uid,
              },
        }

    @api.model
    def create_action(self, domain, title, is_overdue=False):
        domain = domain
        action_ref = 'hr_pms.action_pms_appraisal_view_id'
        search_view_ref = 'hr_pms.view_pms_appraisee_filter'
        action = self.env["ir.actions.actions"]._for_xml_id(action_ref)
        if title:
            action['display_name'] = title
        if search_view_ref:
            action['search_view_id'] = self.env.ref(search_view_ref).read()[0]
        action['views'] = [(False, view) for view in action['view_mode'].split(",")]
        if is_overdue:
            over_dues = self.overdue_pms()
            domain = f"[('id', 'in', {over_dues})]"
        action['domain'] = eval(domain)
        return {'action': action}

    @api.model
    def get_not_generated_employees(self, title):
        def _getpms_not_generated():
            pms = self.env['pms.appraisee'].search([])
            employees = [rec.id for rec in self.env['hr.employee'].search([])]
            pms_employee_ids = [rec.employee_id.id for rec in pms]
            number_of_intersections = []
            for rec in employees:
                if rec not in pms_employee_ids:
                    number_of_intersections.append(rec)
            # number_of_intersections = [emp if emp not in employees else None for emp in pms_employee_ids] # set(employees).intersection(pms_employee_ids)
            return number_of_intersections if number_of_intersections else [0]
        action_ref = 'hr.open_view_employee_list_my'
        search_view_ref = 'hr.view_employee_filter'
        action = self.env["ir.actions.actions"]._for_xml_id(action_ref)
        if title:
            action['display_name'] = title
        if search_view_ref:
            action['search_view_id'] = self.env.ref(search_view_ref).read()[0]
        action['views'] = [(False, view) for view in action['view_mode'].split(",")]
        domain = f"[('id', 'in', {_getpms_not_generated()})]"
        action['domain'] = eval(domain)
        return {'action': action}
    
    # @api.model
    # def create_action(self, action_ref, title, search_view_ref):
    #     action = self.env["ir.actions.actions"]._for_xml_id(action_ref)
    #     if title:
    #         action['display_name'] = title
    #     if search_view_ref:
    #         action['search_view_id'] = self.env.ref(search_view_ref).read()[0]
    #     action['views'] = [(False, view) for view in action['view_mode'].split(",")]
    #     action['domain'] = domain
    #     return {'action': action}

    
        