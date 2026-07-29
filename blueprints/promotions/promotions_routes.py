from flask import Blueprint, render_template, request, jsonify, Request
from flask_htmx import make_response
from sqlalchemy import select, or_
from dateutil.parser import parse
from datetime import date, datetime

import constants
from blueprints.promotions.queries import GetPromotionHistoryStmt, GetStripeNamesByRank, GetStudentRecordsStmtByBadge, \
    UpdateStudentRankStmt, InsertPromotionsRankStmt, GetInsertPromotionDict, GetNextPromotion, \
    DeleteStudentPromotionStmt
from models import Students, Belts, Stripes
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
        return response #render_template('partials/student_names.html', student_list=student_list)


    # search had at least one space, check for badge number
    badge_number = name_search.split()[0]
    print(f'  generating details from badge number: {badge_number}')
    student_list_stmt     = select(Students).where(Students.badgeNumber == badge_number)
    student_list          = db_session.scalars(student_list_stmt).all()
    student_names_html    = render_template('partials/student_names.html', student_list=student_list)

    student_record = student_list[0]
    student_name = f'{student_record.firstName} {student_record.lastName}'

    student_details_html  = render_template('partials/student_details.html',
                                            student_name=student_name,
                                            student_rank=student_record.currentRankName,
                                            student_stripe=student_record.currentStripeName)

    belts_records         = db_session.scalars(select(Belts)).all()

    stripe_records        = (db_session
                             .scalars(select(Stripes)
                                      .where(Stripes.rankNum == student_record.currentRankNum)
                                      .order_by(Stripes.seqNum))
                             .all())
    selection_ranks       = render_template('partials/selection_ranks.html',
                                            belts_records=belts_records,
                                            current_belt_id=student_record.currentRankNum)

    next_promotion        = GetNextPromotion(badge_number)
    selection_stripes     = render_template('partials/selection_stripes.html',
                                            stripe_records=stripe_records,
                                            current_stripe_id=student_record.currentStripeId,
                                            next_stripe_id=next_promotion['stripeId'])

    promotions_list       = GetDataWithArgs(GetPromotionHistoryStmt(), {'badgeNumber' : badge_number})

    promotion_history     = render_template('partials/promotion_history.html',
                                            promotions_list=promotions_list)

    input_promotion_date  = render_template('partials/input_promotion_date.html',
                                            initial_promotion_date=datetime.now().strftime("%Y-%m-%d"))


    response = make_response(student_names_html + student_details_html + selection_ranks + selection_stripes + promotion_history + input_promotion_date)
    return response

@promotions_bp.route('/student_selected')
def student_selected():
    print(f'route: student_selected')

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


