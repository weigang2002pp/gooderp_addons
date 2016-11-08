# -*- coding: utf-8 -*-

from odoo import api, fields, models

# 状态可选值
TASK_STATES = [
    ('todo', u'新建'),
    ('doing', u'正在进行'),
    ('done', u'已完成'),
    ('canceled', u'已取消'),
]


class project(models.Model):
    _name = 'project'

    name = fields.Char(
        string=u'名称',
        required=True,
    )

    task_ids = fields.One2many(
        string=u'任务',
        comodel_name='task',
        inverse_name='project_id',
    )

    customer_id = fields.Many2one(
        string=u'客户',
        comodel_name='partner',
        ondelete='restrict',
    )


class task(models.Model):
    _name = 'task'
    _inherit = ['mail.thread']

    # TODO 继承mail形成跟踪记录

    @api.multi
    def _compute_hours(self):
        self.ensure_one()
        for line in self.env['timeline'].search(
                            [('task_id', '=', self.id)]):
            self.hours += line.hours

    name = fields.Char(
        string=u'名称',
        required=True,
    )

    user_id = fields.Many2one(
        string=u'指派给',
        comodel_name='res.users',
    )

    project_id = fields.Many2one(
        string=u'项目',
        comodel_name='project',
        ondelete='cascade',
    )

    timeline_ids = fields.One2many(
        string=u'工作记录',
        comodel_name='timeline',
        inverse_name='task_id',
    )

    next_action = fields.Char(
        string=u'下一步计划',
        required=False,
        help=u'针对此任务下一步的计划',
        track_visibility='onchange',
    )

    next_datetime = fields.Datetime(
        string=u'下一步计划时间',
        help=u'下一步计划预计开始的时间',
        track_visibility='onchange',
    )

    status = fields.Many2one('task.status',
                             string=u'状态',
                             track_visibility='onchange')
    plan_hours = fields.Float(u'计划时间')
    hours = fields.Float(u'实际时间',
                         compute=_compute_hours)

class task_status(models.Model):
    _name = 'task.status'
    
    name = fields.Char(u'名称')
    state = fields.Selection(TASK_STATES,
                             string=u'任务状态',
                             default='doing')
    sequence = fields.Integer(u'顺序')


class timesheet(models.Model):
    _name = 'timesheet'

    date = fields.Date(
        string=u'日期',
        required=True,
        default=fields.Date.context_today)

    user_id = fields.Many2one(
        string=u'用户',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
        comodel_name='res.users',
    )

    timeline_ids = fields.One2many(
        string=u'工作记录',
        comodel_name='timeline',
        inverse_name='timesheet_id',
    )

    task_ids = fields.Many2many(
        string=u'待办事项',
        required=False,
        readonly=False,
        default=lambda self: [(4, t.id) for t in self.env['task'].search(
                    [('user_id','=',self.env.user.id),
                     ('status.state','=','doing')])],
        help=False,
        comodel_name='task',
        domain=[],
        context={},
        limit=None
    )

    @api.multi
    def name_get(self):
        ret = []
        for s in self:
            ret.append((s.id, '%s %s' % (s.user_id.name, s.date)))
        return ret


class timeline(models.Model):
    _name = 'timeline'

    timesheet_id = fields.Many2one(
        string=u'记录表',
        comodel_name='timesheet',
        ondelete='cascade',
    )

    task_id = fields.Many2one(
        string=u'任务',
        required=True,
        readonly=False,
        comodel_name='task',
    )

    user_id = fields.Many2one(
        string=u'指派给',
        comodel_name='res.users',
    )

    hours = fields.Float(
        string=u'小时数',
        default=0.5,
        digits=(16, 1),
        help=u'实际花的小时数',
    )

    just_done = fields.Char(
        string=u'具体工作内容',
        required=True,
        help=u'在此时长内针对此任务实际完成的工作内容',
    )
# TODO 以下三个字段用于更新task的同名字段
    next_action = fields.Char(
        string=u'下一步计划',
        required=False,
        help=u'针对此任务下一步的计划',
    )

    next_datetime = fields.Datetime(
        string=u'下一步计划时间',
        help=u'下一步计划预计开始的时间',
    )
    set_status = fields.Many2one('task.status',
                             string=u'状态更新到')

    def create(self, vals):
        '''更新task的以下字段'''
        res = super(timeline, self).create(vals)
        set_status = vals.get('set_status')
        task_id = vals.get('task_id')
        next_action = vals.get('next_action')
        next_datetime = vals.get('next_datetime')
        task = self.env['task'].search([('id', '=', task_id)])
        if set_status:
            task.write({'status': set_status})
        if next_action:
            task.write({'next_action': next_action})
        if next_datetime:
            task.write({'next_datetime': next_datetime})
        return res
