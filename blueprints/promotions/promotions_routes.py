from time import sleep

from flask import Blueprint, render_template, request, jsonify, Request
from flask_htmx import make_response
from sqlalchemy import select, or_, func
from dateutil.parser import parse
from datetime import date, datetime

import constants
from blueprints.promotions.promotions_procs import BuildStudentDetailsHtml, BuildAttendanceDetailsHtml, \
    BuildPromotionsInputHtml, BuildPromotionsHistoryHtml, IsDuplicatePromotion, UpdStudentPromotionRecords, \
    BuildRequiredClassesHtml, GetNextPromotionDetails, BuildPromotionsMessageHtml
from blueprints.promotions.queries import GetPromotionHistoryStmt, GetStripeNamesByRank, DeleteStudentPromotionStmt
from models import Students, Belts, Stripes, Requirements, Attendance, Promotions
from sqlite.sqlite_manager import sqlite_manager
from sqlite.sqlite_procs import GetDataNoArgs, GetDataWithArgs

promotions_bp = Blueprint(
    'promotions_bp', __name__,
    template_folder ='templates',
    static_folder   = 'static',
    static_url_path = '/promotions_bp_static'
)

db_session = sqlite_manager().session

@promotions_bp.route('/promotions')
def promotions_bp_home():
    print(f'route: promotions_bp_home')
    return render_template('promotions.html')


@promotions_bp.route('/student_search_by_name')
def student_search_by_name():
    try:
        print(f'route: student_search_by_name')
        name_search = request.args.get("name_search", "").strip().lower()
        print(f'  query: {name_search}')

        # no spaces, the user is typing, populate the datalist/select object
        if name_search.count(" ") == 0:
            print(f'  generating datalist from search: {name_search} ')
            student_list_stmt = select(Students).where(
                or_(Students.firstName.startswith(name_search), Students.lastName.startswith(name_search)))
            student_list = db_session.scalars(student_list_stmt).all()
            response = make_response(render_template('partials/student_names.html', student_list=student_list))
            return response


        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # search had at least one space, check for badge number
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        badge_number = name_search.split()[0]
        #sleep(1)
        student_details_response = make_response(BuildStudentPromotionsScreen(badge_number))
        return student_details_response

    except Exception as ex:
        print(f'{str(ex)}')
        return {'status': 'error', 'message' : str(ex) }

@promotions_bp.route('/get_stripe_names', methods=['GET', 'POST'])
def get_stripe_names():
    print(f'Current route: get_stripe_names')
    sqlQuery      = GetStripeNamesByRank()
    stripeRecords = GetDataWithArgs(sqlQuery, request.json)
    return stripeRecords

@promotions_bp.route('/get_promotion_history', methods=['GET', 'POST'])
def get_promotion_history():
    print(f'Current route: get_promotion_history')
    sqlQuery          = GetPromotionHistoryStmt()
    promotionHistory  = GetDataWithArgs(sqlQuery, request.json)
    return promotionHistory

# --------------------------------------------------------------------
@promotions_bp.route('/save_promotion_date_htmx', methods=['GET', 'POST'])
def save_promotion_date_htmx():
    try:
        promotion_id           = request.args['hdn_promotion_id']
        new_promotion_date     = request.args[f'promotion-date-inp-{promotion_id}']
        new_promotion_date_str = parse(new_promotion_date, fuzzy=False).strftime(constants.fmtDateTime)

        promotion_record_stmt = select(Promotions).where(Promotions.promotionId == promotion_id)
        promotion_record      = db_session.scalars(promotion_record_stmt).first()
        promotion_record.promotionDate  = new_promotion_date_str
        promotion_record.updateDateTime = datetime.now().strftime(constants.fmtDateTime)
        db_session.commit()

        return_message = "Promotion date was updated!"
        response = make_response(return_message)
        response.headers["HX-Trigger"] = '{"resetResponseLabel": "Saved successfully!"}'
        return response
    except Exception as ex:
        print(f'{str(ex)}')
        return {'status': 'error', 'message' : str(ex) }

@promotions_bp.route('/del_promotion_record', methods=['GET', 'POST'])
def del_promotion_record():
    try:
        print(f'request: {request.json['promotionId']}')
        delQuery          = DeleteStudentPromotionStmt()
        #delete_counts     = UpdDataWithArgs(delQuery, {'promotionId': request.json['promotionId']})

        sqlQuery          = GetPromotionHistoryStmt()
        promotionHistory  = GetDataWithArgs(sqlQuery, {'badgeNumber' : request.json['badgeNumber']})
        return {
            'status': 'ok',
            'message' : 'Promotion record was removed',
            'promotionHistory' : promotionHistory
        }
    except Exception as ex:
        print(f'{str(ex)}')
        return {'status': 'error', 'message' : str(ex) }

# --------------------------------------------------------------------
@promotions_bp.route('/get_stripes_htmx', methods=['POST', 'GET'])
def get_stripes_htmx():
    print(f'Current route: get_stripes_htmx')
    print(f'request: {request.args['studentBeltNames']}')
    student_list_stmt       = select(Students).where(Students.badgeNumber == request.args['hdnBadgeNumber'])
    student_record          = db_session.scalars(student_list_stmt).first()

    rank_num                = request.args['studentBeltNames']
    stripe_list_stmt        = select(Requirements).where(Requirements.beltId == rank_num).order_by(Requirements.stripeSeqNum)
    stripe_records          = db_session.scalars(stripe_list_stmt).all()
    input_select_stripes    = render_template('controls/input_select_stripes.html', stripe_records=stripe_records)
    student_record.currentStripeId = stripe_records[0].stripeId
    next_promotion_record   = GetNextPromotionDetails(student_record)
    attendance_counts_html  = BuildAttendanceDetailsHtml (student_record, next_promotion_record)

    return input_select_stripes + attendance_counts_html # render_template('controls/input_select_stripes.html', stripe_records=stripe_records)

# --------------------------------------------------------------------
@promotions_bp.route('/upd_requirements_htmx', methods=['GET', 'POST'])
def upd_requirements_htmx():
    print(f'Current route: upd_requirements_htmx')
    student_list_stmt       = select(Students).where(Students.badgeNumber == request.args['hdnBadgeNumber'])
    student_record          = db_session.scalars(student_list_stmt).first()
    next_promotion_record   = GetNextPromotionDetails(student_record)
    attendance_counts_html  = BuildAttendanceDetailsHtml (student_record, next_promotion_record)
    return attendance_counts_html

# --------------------------------------------------------------------
@promotions_bp.route('/upd_student_rank_htmx', methods=['GET', 'POST'])
def upd_student_rank_htmx():
    try:
        print(f'Current route: upd_student_rank_htmx')
        student_list_stmt       = select(Students).where(Students.badgeNumber == request.args['hdnBadgeNumber'])
        student_record          = db_session.scalars(student_list_stmt).first()

        belt_id        = request.args['studentBeltNames']
        stripe_id      = request.args['studentBeltStripes']
        promotion_date = parse(request.args['studentPromotionDate'], fuzzy=False) #.date()

        # do not apply if no changes
        request_json = {
            'beltId'        : belt_id,
            'stripeId'      : stripe_id,
            'promotionDate' : promotion_date
        }
        if IsDuplicatePromotion(student_record, request_json):
            return_message = "No changes to save!"
            response = make_response(return_message)
            response.headers["HX-Trigger"] = '{"resetResponseLabel": "Saved successfully!"}'

        # update the student record from the new data
        UpdStudentPromotionRecords(student_record, int(belt_id), int(stripe_id), promotion_date)

        return_message = "Student record was updated!"
        student_details_html = BuildStudentPromotionsScreen(student_record.badgeNumber)
        response = make_response(return_message + student_details_html)
        response.headers["HX-Trigger"] = '{"resetResponseLabel": "Saved successfully!"}'
        return response
    except Exception as ex:
        print(f'{constants.consoleRed}{str(ex)}')
        return {'status': 'error', 'message': str(ex)}


def BuildStudentPromotionsScreen(badge_number):
    try:
        print(f'  generating details from badge number: {badge_number}')
        student_list_stmt = select(Students).where(Students.badgeNumber == badge_number)
        student_record = db_session.scalars(student_list_stmt).all()[0]

        next_promotion_record  = GetNextPromotionDetails(student_record)

        student_details_html   = BuildStudentDetailsHtml(student_record)
        attendance_counts_html = BuildAttendanceDetailsHtml(student_record, next_promotion_record)
        required_counts_html   = BuildRequiredClassesHtml(student_record, next_promotion_record)
        student_promotion_html = BuildPromotionsInputHtml(student_record, next_promotion_record)
        promotion_history_html = BuildPromotionsHistoryHtml(student_record)
        promotion_message_html = BuildPromotionsMessageHtml(next_promotion_record.promotion_message)
        return (student_details_html +
                attendance_counts_html +
                student_promotion_html +
                promotion_history_html +
                required_counts_html +
                promotion_message_html)
    except Exception as ex:
        print(f'Error: {str(ex)}')
        return {'status': 'error', 'message': str(ex)}
