from flask import Blueprint, render_template, request, jsonify, Request
from flask_htmx import make_response
from sqlalchemy import select, or_, func
from dateutil.parser import parse
from datetime import date, datetime

import constants
from blueprints.promotions.promotions_procs import BuildStudentDetailsHtml, BuildAttendanceDetailsHtml, \
    BuildPromotionsInputHtml, BuildPromotionsHistoryHtml
from blueprints.promotions.queries import GetPromotionHistoryStmt, GetStripeNamesByRank, GetStudentRecordsStmtByBadge, \
    UpdateStudentRankStmt, InsertPromotionsRankStmt, GetInsertPromotionDict, GetNextPromotion, \
    DeleteStudentPromotionStmt
from models import Students, Belts, Stripes, Requirements, Attendance
from sqlite.sqlite_alchemy import getAlchemySession
from sqlite.sqlite_procs import GetDataNoArgs, GetDataWithArgs, UpdDataWithArgs

promotions_bp = Blueprint(
    'promotions_bp', __name__,
    template_folder ='templates',
    static_folder   = 'static',
    static_url_path = '/promotions_bp_static'
)

db_session = getAlchemySession()

@promotions_bp.route('/promotions')
def promotions_bp_home():
    print(f'route: promotions_bp_home')
    return render_template('promotions.html')


@promotions_bp.route('/student_search_by_name')
def student_search_by_name():
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
    print(f'  generating details from badge number: {badge_number}')
    student_list_stmt       = select(Students).where(Students.badgeNumber == badge_number)
    student_record          = db_session.scalars         (student_list_stmt).all()[0]
    student_details_html    = BuildStudentDetailsHtml    (student_record)
    attendance_counts_html  = BuildAttendanceDetailsHtml (student_record)
    student_promotion_html  = BuildPromotionsInputHtml   (student_record)
    promotion_history_html  = BuildPromotionsHistoryHtml (student_record)

    response = make_response(
        student_details_html + attendance_counts_html + student_promotion_html + promotion_history_html
    )
    return response  #student_details_html + attendance_counts_html + student_promotion_html + promotion_history_html

@promotions_bp.route('/get_stripe_names', methods=['GET', 'POST'])
def get_stripe_names():
    print(f'Current route: get_stripe_names')
    sqlQuery      = GetStripeNamesByRank()
    stripeRecords = GetDataWithArgs(sqlQuery, request.json)
    return stripeRecords


@promotions_bp.route('/upd_student_rank', methods=['GET', 'POST'])
def upd_student_rank():
    print(f'Current route: upd_student_rank')
    studentData       = GetDataWithArgs(GetStudentRecordsStmtByBadge(), {'badgeNumber': request.json['badgeNumber']})
    promotionHistory  = GetDataWithArgs(GetPromotionHistoryStmt(), request.json)

    # do not apply if no changes
    if IsDuplicatePromotion(studentData, request.json):
        return {'status': 'error', 'badgeNumber': request.json['badgeNumber'],
                'message': 'Current promotion matches last promotion!'}

    updStudentQuery   = UpdateStudentRankStmt()
    updStudentDict    = {
        'currentRankNum'    : request.json['beltId'],
        'currentRankName'   : request.json['beltTitle'],
        'currentStripeId'   : request.json['stripeId'],
        'currentStripeName' : request.json['stripeTitle'],
        'badgeNumber'       : request.json['badgeNumber'],
        # 'studentPromotionDate': request.json['promotionDate']
    }

    # adjust the date to consistent format
    studentPromotionDate = parse(request.json['promotionDate'], fuzzy=False).strftime(constants.fmtDateTime)
    updStudentDict['studentPromotionDate'] = studentPromotionDate
    updStudentDict['comments'] = 'Promotion'

    # update the student record
    updateCounts = UpdDataWithArgs(updStudentQuery, updStudentDict)

    #insert the history record
    insertPromotionStmt = InsertPromotionsRankStmt()
    insertPromotionDict = GetInsertPromotionDict(studentData, updStudentDict)
    insertCounts        = UpdDataWithArgs(insertPromotionStmt, insertPromotionDict)

    return {'status': 'ok',
            'badgeNumber': request.json['badgeNumber'],
            'lastRowId': updateCounts['lastrowid'],
            'rowCount': updateCounts['rowcount']
            }

def IsDuplicatePromotion(studentData, requestJson) -> bool:
    if studentData[0]['currentRankNum'] is None:
        return False

    currentRankNum   = int(studentData[0]['currentRankNum'])
    selectedBeltId   = int(requestJson['beltId'])
    currentStripeId  = int(studentData[0]['currentStripeId'])
    selectedStripeId = int(requestJson['stripeId'])

    if studentData[0]['studentPromotionDate'] is None:
        currentPromotionDate = datetime.fromisoformat("1900-01-01T00:00:00")
    else:
        currentPromotionDate = parse(studentData[0]['studentPromotionDate'], fuzzy=False).date()

    selectedPromotionDate = parse(request.json['promotionDate'], fuzzy=False).date()

    if (   currentRankNum == selectedBeltId
       and currentStripeId == selectedStripeId
       and currentPromotionDate == selectedPromotionDate):
        return True

    return False

@promotions_bp.route('/get_promotion_history', methods=['GET', 'POST'])
def get_promotion_history():
    print(f'Current route: get_promotion_history')
    sqlQuery          = GetPromotionHistoryStmt()
    promotionHistory  = GetDataWithArgs(sqlQuery, request.json)
    return promotionHistory

# --------------------------------------------------------------------
@promotions_bp.route('/del_promotion_record', methods=['GET', 'POST'])
def del_promotion_record():
    try:
        print(f'request: {request.json['promotionId']}')
        delQuery          = DeleteStudentPromotionStmt()
        delete_counts     = UpdDataWithArgs(delQuery, {'promotionId': request.json['promotionId']})

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
    student_record          = db_session.scalars         (student_list_stmt).all()[0]

    rank_num                = request.args['studentBeltNames']
    stripe_list_stmt        = select(Requirements).where(Requirements.beltId == rank_num).order_by(Requirements.stripeSeqNum)
    stripe_records          = db_session.scalars(stripe_list_stmt).all()
    input_select_stripes    = render_template('controls/input_select_stripes.html', stripe_records=stripe_records)
    student_record.currentStripeId = stripe_records[0].stripeId
    attendance_counts_html  = BuildAttendanceDetailsHtml (student_record)

    return input_select_stripes + attendance_counts_html # render_template('controls/input_select_stripes.html', stripe_records=stripe_records)

# --------------------------------------------------------------------
@promotions_bp.route('/upd_requirements_htmx', methods=['GET', 'POST'])
def upd_requirements_htmx():
    print(f'Current route: upd_requirements_htmx')
    student_list_stmt       = select(Students).where(Students.badgeNumber == request.args['hdnBadgeNumber'])
    student_record          = db_session.scalars         (student_list_stmt).all()[0]
    attendance_counts_html  = BuildAttendanceDetailsHtml (student_record)
    return attendance_counts_html

# --------------------------------------------------------------------
@promotions_bp.route('/upd_student_rank_htmx', methods=['GET', 'POST'])
def upd_student_rank_htmx():
    print(f'Current route: upd_student_rank_htmx')
    student_list_stmt       = select(Students).where(Students.badgeNumber == request.args['hdnBadgeNumber'])
    student_record          = db_session.scalars         (student_list_stmt).all()[0]
    selected_stripe_id      = request.args['studentBeltStripes']

    # do not apply if no changes
    # if IsDuplicatePromotion(student_record, request.json):
    #     return {'status': 'error', 'badgeNumber': request.json['badgeNumber'],
    #             'message': 'Current promotion matches last promotion!'}


    response = make_response("Student record was updated!")
    response.headers["HX-Trigger"] = '{"resetResponseLabel": "Saved successfully!"}'
    return response
