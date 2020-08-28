import sys
import json
import requests
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    flash
)
from flask_wtf import FlaskForm
from wtforms import HiddenField
from datetime import date, datetime, timedelta

from app.mod_calendar.calendar import Calendar
from app.mod_calendar.forms import CalendarForm, TaskForm
import app.mod_auth.auth as auth

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_calendar = Blueprint('calendar', __name__, url_prefix='/calendar')


@mod_calendar.errorhandler(400)
def permission_error(error):
    return render_template('errors/400.html', error_msg=error), 400


@mod_calendar.errorhandler(401)
def authorization_error(error):
    return render_template('errors/401.html', error_msg=error), 401


@mod_calendar.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', error_msg=error), 404


@mod_calendar.errorhandler(422)
def unprocessable_entity_error(error):
    return render_template('errors/422.html', error_msg=error), 422


@mod_calendar.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html', error_msg=error), 500


def get_jwt_token():
    token = None
    if 'jwt_token' in session:
        token = session['jwt_token']
    return token


def api_request(
    method,
    api,
    data=None,
    headers={'content-type': 'application/json'}
):
    if get_jwt_token():
        headers['Authorization'] = 'Bearer %s' % get_jwt_token()
    else:
        headers.pop('Authorization', None)
    url = current_app.config["API_URL"] + 'api' + api
    if method.upper() == 'GET':
        response = requests.get(url=url, headers=headers).json()
    elif method.upper() == 'POST':
        response = requests.post(url=url, data=data, headers=headers).json()
    elif method.upper() == 'PATCH':
        response = requests.patch(url=url, data=data, headers=headers).json()
    elif method.upper() == 'DELETE':
        response = requests.delete(url=url, headers=headers).json()
    else:
        return False, server_error('Internal server error')

    if response.get('success', False) is False:
        if response.get('error', None) == 400:
            return False, permission_error('Permission denied')
        elif response.get('error', None) == 401:
            return False, authorization_error('Not authorized')
        elif response.get('error', None) == 404:
            return False, not_found_error('Resource not found')
        elif response.get('error', None) == 422:
            return False, unprocessable_entity_error('Unprocessable request')
        elif response.get('error', None) == 500:
            return False, server_error('Internal server error')
    return True, response


@mod_calendar.route('/', methods=['GET'])
def index():
    ret, response = api_request('GET', '/calendars/')
    if ret is False:
        flash('No calendars found')
        return response

    class MyCSRFForm(FlaskForm):
        id = HiddenField('id')

    return render_template(
        'calendar/home.html',
        session=session,
        calendars=response['calendars'],
        form=MyCSRFForm(),
        api_url=current_app.config["API_URL"] + 'api',
        dashboard_link='/auth/dashboard',
        jwt=get_jwt_token()
    )


@mod_calendar.route('/<int:calendar_id>/', methods=['GET'])
def get_calendar_id(calendar_id):
    y = request.args.get('y', -1, type=int)
    m = request.args.get('m', -1, type=int)
    if y != -1 and m != -1:
        ret, response = api_request(
            'GET', '/calendars/%d/tasks/?y=%d&m=%d' % (calendar_id, y, m))
    else:
        ret, response = api_request(
            'GET', '/calendars/%d/tasks/' % calendar_id)
    if ret is False:
        flash('Calendar %s not found' % calendar_id)
        return response

    def _add_task_to_task_list(
        tasks_list,
        day,
        month,
        task,
        view_past_tasks=True
    ):
        if not view_past_tasks:
            # Check if this task should be hidden
            start_time = datetime.now()
            end_time = datetime.strptime(
                task['end_time'], '%Y-%m-%d, %H:%M:%S')
            task_end_time = datetime(
                start_time.year,
                month, day,
                end_time.hour,
                end_time.minute,
                end_time.second
            )
            if task_end_time < start_time:
                return
        if month not in tasks_list:
            tasks_list[month] = {}
        if day not in tasks_list[month]:
            tasks_list[month][day] = []
        tasks_list[month][day].append(task)

    week_starting_day = response['calendar']['week_starting_day']
    Calendar.set_first_weekday(week_starting_day)

    year = response['year']
    month = response['month']
    month_name = Calendar.month_name(month)
    min_year = response['calendar']['min_year']
    max_year = response['calendar']['max_year']
    view_past_tasks = response['calendar']['hide_past_tasks']
    month_days = Calendar.month_days(year, month)
    weekdays_headers = Calendar.weekdays(week_starting_day)

    tasks = {}
    for task in response['tasks']:
        if task['is_recurrent']:
            monthly_repetition_done = False
            for week in Calendar.month_days_with_weekday(year, month):
                for weekday, day in enumerate(week):
                    if day == 0:
                        continue
                    if task['repetition_type'] == 'w':
                        # Weekly repetition: repetition_value is a week day
                        if task['repetition_value'] == weekday:
                            _add_task_to_task_list(
                                tasks, day, month, task, view_past_tasks)
                    elif task['repetition_type'] == 'm':
                        if task['repetition_subtype'] == 'w':
                            # Monthly repetition: repetition_value is a
                            # week day
                            if (
                                task['repetition_value'] == weekday
                                and not monthly_repetition_done
                            ):
                                _add_task_to_task_list(
                                    tasks, day, month, task, view_past_tasks)
                                monthly_repetition_done = True
                        elif task['repetition_subtype'] == 'm':
                            # Monthly repetition: repetition_value is a day
                            if task['repetition_value'] == day:
                                _add_task_to_task_list(
                                    tasks, day, month, task, view_past_tasks)
        else:
            start_time = datetime.strptime(
                task['start_time'], '%Y-%m-%d, %H:%M:%S')
            task_day = start_time.day
            task_month = start_time.month
            _add_task_to_task_list(tasks, task_day, task_month, task)

    return render_template(
        "calendar/calendar.html",
        session=session,
        calendar_id=response['calendar']['id'],
        calendar_name=response['calendar']['name'],
        year=year,
        month=month,
        month_name=month_name,
        current_date=datetime.date(datetime.now()),
        month_days=month_days,
        previous_month_link=Calendar.previous_month_link(
            year, month, min_year, max_year),
        next_month_link=Calendar.next_month_link(
            year, month, min_year, max_year),
        tasks=tasks,
        display_view_past_button=response['calendar']['show_view_past_btn'],
        hide_past_tasks=response['calendar']['hide_past_tasks'],
        weekdays_headers=weekdays_headers,
        dashboard_link='/auth/dashboard',
        api_url=current_app.config["API_URL"] + 'api',
        jwt=get_jwt_token()
    )


@mod_calendar.route('/create', methods=['GET'])
# @auth.requires_auth('post:calendars')
def new_calendar():  # jwt):
    form = CalendarForm()
    form.calendar_id.default = 0
    form.process()
    return render_template("calendar/calendar_form.html", form=form)


@mod_calendar.route('/create', methods=['POST'])
# @auth.requires_auth('post:calendars')
def save_calendar():  # jwt):
    try:
        form = CalendarForm()
        if form.validate():
            calendar = {
                'name': form.name.data,
                'description': form.description.data,
                'min_year': int(form.min_year.data),
                'max_year': int(form.max_year.data),
                'time_zone': form.time_zone.data,
                'week_starting_day': int(form.week_starting_day.data),
                'emojis_enabled': form.emojis_enabled.data,
                'show_view_past_btn': form.show_view_past_btn.data
            }
            ret, response = api_request(
                'POST', '/calendars/', json.dumps(calendar))
            if ret is True:
                flash('Calendar ' + form.name.data +
                      ' was successfully created!')
                return redirect(
                    "/calendar/%d" % (response['calendar_id']),
                    code=302
                )
        else:
            error_msg = ''
            if form.errors:
                for key, value in form.errors.items():
                    error_msg += ' -' + key + ': ' + value[0]
            if len(error_msg):
                flash('Error! Calendar ' + form.name.data +
                      ' contains invalid data!' + error_msg)
            return render_template("calendar/calendar_form.html", form=form)
    except Exception:
        print("Unexpected error:", sys.exc_info()[0])
        return unprocessable_entity_error('Calendar not created')


@mod_calendar.route('/<int:calendar_id>/delete', methods=['DELETE'])
# @auth.requires_auth('delete:calendars')
def delete_calendar(calendar_id):
    ret, response = api_request('DELETE', '/calendars/%d/' % calendar_id)
    if ret is False:
        flash('Calendar %s not found' % calendar_id)
        return response
    name = response['name']
    flash('Calendar ' + name + ' was successfully deleted!')
    return redirect("/calendar/", code=302)


@mod_calendar.route('/<int:calendar_id>/edit', methods=['GET'])
# @auth.requires_auth('patch:calendars')
def edit_calendar_form(calendar_id):
    ret, response = api_request('GET', '/calendars/%d/' % calendar_id)
    if ret is False:
        flash('Calendar %s not found' % calendar_id)
        return response
    calendar = response['calendar']

    form = CalendarForm()
    form.calendar_id.default = calendar['id']
    form.name.default = calendar['name']
    form.description.default = calendar['description']
    form.min_year.default = calendar['min_year']
    form.max_year.default = calendar['max_year']
    form.time_zone.default = calendar['time_zone']
    form.week_starting_day.default = calendar['week_starting_day']
    form.time_zone.default = calendar['time_zone']
    form.emojis_enabled.default = calendar['emojis_enabled']
    form.show_view_past_btn.default = calendar['show_view_past_btn']
    form.process()

    return render_template("calendar/calendar_form.html", form=form)


@mod_calendar.route('/<int:calendar_id>/edit', methods=['POST'])
# @auth.requires_auth('post:calendars')
def save_calendar_form(calendar_id):
    form = CalendarForm()
    if not form.validate():
        error_msg = ''
        if form.errors:
            for key, value in form.errors.items():
                error_msg += ' -' + key + ': ' + value[0]
        if len(error_msg):
            flash('Error! Calendar ' + form.name.data +
                  ' contains invalid data!' + error_msg)
        return render_template(
            "calendar/calendar_form.html",
            calendar=vars(calendar_query),
            form=form)

    calendar = {}
    calendar['id'] = int(form.calendar_id.data)
    calendar['name'] = form.name.data
    calendar['description'] = form.description.data
    calendar['min_year'] = int(form.min_year.data)
    calendar['max_year'] = int(form.max_year.data)
    calendar['time_zone'] = form.time_zone.data
    calendar['week_starting_day'] = int(form.week_starting_day.data)
    calendar['emojis_enabled'] = form.emojis_enabled.data
    calendar['show_view_past_btn'] = form.show_view_past_btn.data

    ret, response = api_request(
        'PATCH', '/calendars/%d/' % calendar_id, json.dumps(calendar))
    if ret is False:
        flash('Calendar %s not updated' % calendar_id)
        return response

    flash('Calendar ' + form.name.data + ' was successfully saved!')
    return redirect("/calendar/%d" % (calendar_id), code=302)


@mod_calendar.route('/<int:calendar_id>/tasks', methods=['GET'])
# @auth.requires_auth('post:tasks')
def new_task_form(calendar_id):
    ret, calendar_query = api_request('GET', '/calendars/%d/' % calendar_id)
    if ret is False:
        flash('Calendar %s not found' % calendar_id)
        return response

    Calendar.set_first_weekday(calendar_query['calendar']['week_starting_day'])

    min_year = calendar_query['calendar']['min_year']
    max_year = calendar_query['calendar']['max_year']

    year = int(request.args.get("year", datetime.now().year))
    month = int(request.args.get("month", datetime.now().month))
    current_day, current_month, current_year = Calendar.current_date()
    year = max(min(year, max_year), min_year)
    month = max(min(month, 12), 1)

    if current_month == month and current_year == year:
        day = current_day
    else:
        day = 1
    day = int(request.args.get("day", day))

    start_time = datetime(year, month, day)
    end_time = start_time + timedelta(hours=23, minutes=59, seconds=59)
    task = {
        'calendar_id': calendar_id,
        'title': '',
        'color': current_app.config["BUTTON_CUSTOM_COLOR_VALUE"],
        'details': '',
        'start_time': start_time,
        'end_time': end_time,
        'is_all_day': True,
        'is_recurrent': False,
        'repetition_value': 0,
        'repetition_type': '',
        'repetition_subtype': ''
    }

    taskForm = TaskForm()
    taskForm.task_id.default = 0
    taskForm.calendar_id.default = calendar_id
    taskForm.title.default = ''
    taskForm.color.default = current_app.config["BUTTON_CUSTOM_COLOR_VALUE"]
    taskForm.details.default = ''
    taskForm.start_date.default = start_time.strftime("%H:%M:%S")
    taskForm.start_time.default = start_time.strftime("%d/%m/%Y")
    taskForm.end_date.default = end_time.strftime("%H:%M:%S")
    taskForm.end_time.default = end_time.strftime("%d/%m/%Y")
    taskForm.is_all_day.default = True
    taskForm.is_recurrent.default = False
    taskForm.repetition_value.default = 0
    taskForm.repetition_type.default = ''
    taskForm.repetition_subtype.default = ''
    taskForm.process()

    if calendar_query['calendar']['emojis_enabled']:
        emojis_list = current_app.config["BUTTONS_EMOJIS_LIST"]
    else:
        emojis_list = tuple()

    return render_template(
        "calendar/task.html",
        form=taskForm,
        calendar_id=calendar_id,
        year=year,
        month=month,
        min_year=min_year,
        max_year=max_year,
        month_names=Calendar.month_names(),
        task=task,
        emojis_enabled=calendar_query['calendar']['emojis_enabled'],
        button_default_color_value=current_app.config[
            "BUTTON_CUSTOM_COLOR_VALUE"
        ],
        buttons_colors=current_app.config["BUTTONS_COLORS_LIST"],
        buttons_emojis=emojis_list,
        api_url=current_app.config["API_URL"] + 'api'
    )


@mod_calendar.route('/<int:calendar_id>/tasks', methods=['POST'])
# @auth.requires_auth('post:tasks')
def create_task(calendar_id):
    title = request.form["title"].strip()
    start_date = request.form.get("start_date", "")
    end_date = request.form.get("end_date", "")

    if len(start_date) > 0 and len(end_date) > 0:
        date_fragments = start_date.split('-')
        year = int(date_fragments[0])
        month = int(date_fragments[1])
        day = int(date_fragments[2])

        is_all_day = request.form.get("is_all_day", "0") == "1"
        start_time = request.form["start_time"]
        end_time = request.form.get("end_time", None)
        details = request.form["details"].replace(
            "\r", "").replace("\n", "<br>")
        color = request.form["color"]
        is_recurrent = request.form.get("repeats", "0") == "1"
        repetition_type = request.form.get("repetition_type")
        repetition_subtype = request.form.get("repetition_subtype")
        repetition_value = int(request.form["repetition_value"])

        newTask = {
            'calendar_id': calendar_id,
            'title': title,
            'color': color,
            'details': details,
            'start_time': start_date + ', ' + start_time,
            'end_time': end_date + ', ' + end_time,
            'is_all_day': is_all_day,
            'is_recurrent': is_recurrent,
            'repetition_value': repetition_value,
            'repetition_type': repetition_type,
            'repetition_subtype': repetition_subtype
        }
        ret, response = api_request(
            'POST', '/calendars/tasks/', json.dumps(newTask))
        if ret is False:
            flash('Task in calendar %s not created' % calendar_id)
            return response

        return redirect(
            "/calendar/%s/?y=%d&m=%d" % (calendar_id, year, month),
            code=302
        )
    else:
        return redirect("/calendar/%s" % (calendar_id), code=302)


@mod_calendar.route('/<int:calendar_id>/tasks/<int:task_id>', methods=['GET'])
# @auth.requires_auth('patch:tasks')
def edit_task(calendar_id, task_id):
    ret, response = api_request('GET', '/calendars/tasks/%d/' % task_id)
    if ret is False:
        flash('Task %s not found' % task_id)
        return response

    task = response['task']
    calendar = response['calendar']

    if task['details'] == "&nbsp;":
        task['details'] = ""

    start_time = datetime.strptime(task['start_time'], '%Y-%m-%d, %H:%M:%S')
    end_time = datetime.strptime(task['end_time'], '%Y-%m-%d, %H:%M:%S')
    task['start_time'] = start_time
    task['end_time'] = end_time

    taskForm = TaskForm()
    taskForm.task_id.default = task['id']
    taskForm.calendar_id.default = task['calendar_id']
    taskForm.title.default = task['title']
    taskForm.color.default = task['color']
    taskForm.details.default = task['details']
    taskForm.start_date.default = start_time.date
    taskForm.start_time.default = start_time.time
    taskForm.end_date.default = end_time.date
    taskForm.end_time.default = end_time.time
    taskForm.is_all_day.default = task['is_all_day']
    taskForm.is_recurrent.default = task['is_recurrent']
    taskForm.repetition_value.default = task['repetition_value']
    taskForm.repetition_type.default = task['repetition_type']
    taskForm.repetition_subtype.default = task['repetition_subtype']
    taskForm.process()

    if calendar_query['calendar']['emojis_enabled']:
        emojis_list = current_app.config["BUTTONS_EMOJIS_LIST"]
    else:
        emojis_list = tuple()

    return render_template(
        "calendar/task.html",
        form=taskForm,
        calendar_id=calendar_id,
        year=request.args.get("year"),
        month=request.args.get("month"),
        min_year=calendar['min_year'],
        max_year=calendar['max_year'],
        month_names=Calendar.month_names(),
        task=task,
        emojis_enabled=calendar['emojis_enabled'],
        button_default_color_value=current_app.config[
            "BUTTON_CUSTOM_COLOR_VALUE"
        ],
        buttons_colors=current_app.config["BUTTONS_COLORS_LIST"],
        buttons_emojis=emojis_list,
        api_url=current_app.config["API_URL"] + 'api',
        jwt=get_jwt_token()
    )


@mod_calendar.route('/<int:calendar_id>/tasks/<int:task_id>', methods=['POST'])
# @auth.requires_auth('patch:tasks')
def update_task(calendar_id, task_id):
    title = request.form["title"].strip()
    color = request.form["color"]
    details = request.form["details"].replace("\r", "").replace("\n", "<br>")
    start_date = request.form["start_date"]
    start_time = request.form["start_time"]
    end_date = request.form["end_date"]
    end_time = request.form["end_time"]
    is_all_day = request.form.get("is_all_day", "0") == "1"
    is_recurrent = request.form.get("repeats", "0") == "1"
    repetition_value = int(request.form["repetition_value"])
    repetition_type = request.form.get("repetition_type", "")
    repetition_subtype = request.form.get("repetition_subtype", "")

    try:
        task = Task.getTask(task_id)
        if task is None:
            return not_found_error('Task %s not found' % task_id)

        task.calendar_id = calendar_id
        task.title = title
        task.color = color
        task.details = details
        task.start_time = datetime.strptime(
            '%s %s' % (start_date, start_time), '%Y-%m-%d %H:%M')
        task.end_time = datetime.strptime(
            '%s %s' % (end_date, end_time), '%Y-%m-%d %H:%M')
        task.is_all_day = is_all_day
        task.is_recurrent = is_recurrent
        task.repetition_value = repetition_value
        task.repetition_type = repetition_type
        task.repetition_subtype = repetition_subtype

        task.update()
    except Exception:
        print("Unexpected error:", sys.exc_info()[0])
        return unprocessable_entity_error('Task %s not saved' % task_id)

    return redirect(
        "/calendar/%d?y=%d&m=%d" % (
            calendar_id,
            task.start_time.year,
            task.start_time.month
        ),
        code=302
    )


@mod_calendar.route(
    '/<int:calendar_id>/tasks/<int:task_id>',
    methods=['PATCH']
)
# @auth.requires_auth('patch:tasks')
def update_task_day(calendar_id, task_id):
    body = request.get_json()
    newDay = int(body.get('newDay'))
    try:
        task = Task.getTask(task_id)
        if task is None:
            return not_found_error('Task %s not found' % task_id)
        if newDay:
            task.start_time = task.start_time.replace(day=newDay)
            task.end_time = task.end_time.replace(day=newDay)
            task.update()
    except Exception:
        print("Unexpected error:", sys.exc_info()[0])
        return unprocessable_entity_error('Task %s not saved' % task_id)

    return jsonify({
        'success': True,
        'task_id': task_id
    })


@mod_calendar.route(
    '/<int:calendar_id>/tasks/<int:task_id>',
    methods=['DELETE']
)
# @auth.requires_auth('delete:tasks')
def delete_task(calendar_id, task_id):
    try:
        task = Task.getTask(task_id)
        if task is None:
            return not_found_error('Task %s not found' % task_id)
        task.delete()
    except Exception:
        print("Unexpected error:", sys.exc_info()[0])
        return unprocessable_entity_error('Task %s not saved' % task_id)

    return jsonify({
        'success': True,
        'task_id': task_id
    })
