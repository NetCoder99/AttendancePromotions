from flask import render_template
#from flask_htmx import make_response
from sqlalchemy import select, func
from datetime import datetime
import traceback

#from blueprints.promotions.queries import GetNextPromotion
from dateutil.parser import parse, ParserError
from sqlalchemy.orm import Session

import constants
from models import Students, Requirements, Attendance, Belts, Promotions, NextPromotion
from sqlite.sqlite_alchemy import getAlchemySession
from sqlite.sqlite_manager import sqlite_manager

db_session = sqlite_manager().session

def BuildStudentDetailsHtml(student_record: Students):
    student_list_stmt     = select(Students).where(Students.badgeNumber == student_record.badgeNumber)
    student_record        = db_session.scalars(student_list_stmt).all()[0]
    student_name = f'{student_record.firstName} {student_record.lastName}'

    CheckStudentRank(student_record)

    student_details_html  = render_template('partials/student_details.html',
                                            badge_number=student_record.badgeNumber,
                                            student_name=student_name,
                                            student_rank=student_record.currentRankName,
                                            student_stripe=student_record.currentStripeName)
    return student_details_html

def BuildAttendanceDetailsHtml(student_record: Students, next_promotion_record: NextPromotion):
    try:
        CheckStudentRank(student_record)
        requirements_counts    = render_template(
            "partials/attendance_counts.html",
            total_attendance_count  = next_promotion_record.attendance_count_total,
            belt_attendance_count   = next_promotion_record.attendance_count_since_belt,
            stripe_attendance_count = next_promotion_record.attendance_count_since_stripe
        )
        return requirements_counts
    except Exception as ex:
        print(f'Error: {str(ex)}')
        raise ex

def BuildRequiredClassesHtml(student_record: Students, next_promotion_record: NextPromotion):
    try:
        CheckStudentRank(student_record)
        requirements_counts    = render_template(
            "partials/required_counts.html",
            total_classes_required  = next_promotion_record.classes_until_from_total,
            belt_classes_required   = next_promotion_record.classes_until_from_belt,
            stripe_classes_required = next_promotion_record.classes_until_from_stripe
        )
        return requirements_counts
    except Exception as ex:
        print(f'Error: {str(ex)}')
        raise ex

def BuildPromotionsInputHtml(student_record: Students, next_promotion_record: NextPromotion):
    try:
        if not student_record.currentRankNum:
            requirement_record = (db_session
                                  .scalars(select(Requirements)
                                           .where(Requirements.beltId == 1)
                                           .order_by(Requirements.stripeSeqNum))
                                  .all())[0]
            student_record.currentRankNum = requirement_record.beltId
            student_record.currentRankName = requirement_record.beltTitle
            student_record.currentStripeId = requirement_record.stripeId
            student_record.currentStripeName = requirement_record.stripeTitle

        belts_records         = db_session.scalars(select(Belts)).all()
        current_requirement_record = (
            db_session.scalars(select(Requirements).where(Requirements.stripeId == student_record.currentStripeId))
            .first()
        )

        # get the belts/stripes for the next promotion
        next_requirement_stmt = (select(Requirements)
                                 .where(Requirements.requirementId > current_requirement_record.requirementId)
        )
        next_requirement_record = (
            db_session.scalars(next_requirement_stmt)
            .first()
        )
        stripe_records        = (db_session
                                 .scalars(select(Requirements)
                                          .where(Requirements.beltId == next_requirement_record.beltId)
                                          .order_by(Requirements.stripeSeqNum))
                                 .all())

        student_promotions    = render_template('partials/student_promotions.html',
                                                belts_records     = belts_records,
                                                current_belt_id   = student_record.currentRankNum,
                                                next_belt_id      = next_requirement_record.beltId,
                                                stripe_records    = stripe_records,
                                                current_stripe_id = student_record.currentStripeId,
                                                next_stripe_id    = next_requirement_record.stripeId,
                                                initial_promotion_date=datetime.now().strftime("%Y-%m-%d"))
        return student_promotions
    except Exception as ex:
        print(f'Error: {str(ex)}')
        traceback.print_exc()
        raise ex

def BuildPromotionsHistoryHtml(student_record: Students):
    promotion_list   = (db_session
                             .scalars(select(Promotions)
                                      .where(Promotions.badgeNumber == student_record.badgeNumber)
                                      .order_by(Promotions.promotionId.desc()))
                             .all())
    promotion_history     = render_template('partials/promotion_history.html',
                                            promotions_list=promotion_list)
    return promotion_history

def BuildPromotionsMessageHtml(promotion_message: str):
    return render_template('partials/promotion_message.html', promotion_message=promotion_message)

# -----------------------------------------------------------------------------------
# during development the student rank/stripe is not reliably set
# -----------------------------------------------------------------------------------
def CheckStudentRank(student_record: Students):
    try:
        # if both rank and stripe are not set then check for a promotion record, use that if found
        # else default to white belt with no stripe
        if not student_record.currentRankNum and not student_record.currentStripeId:
            promotion_record_stmt = (select(Promotions)
                                     .where(Promotions.badgeNumber == student_record.badgeNumber)
                                     .order_by(Promotions.promotionDate.desc()))
            promotion_record = db_session.scalars(promotion_record_stmt).first()
            if promotion_record:
                student_record.currentRankNum     = promotion_record.beltId
                student_record.currentRankName    = promotion_record.beltTitle
                student_record.currentStripeId    = promotion_record.stripeId
                student_record.currentStripeName  = promotion_record.stripeTitle
                student_record.studentPromotionDate = promotion_record.promotionDate
            else:
                requirement_record = (db_session
                                  .scalars(select(Requirements)
                                           .where(Requirements.beltId == 1)
                                           .order_by(Requirements.stripeSeqNum))
                                  .all())[0]
                student_record.currentRankNum     = requirement_record.beltId
                student_record.currentRankName    = requirement_record.beltTitle
                student_record.currentStripeId    = requirement_record.stripeId
                student_record.currentStripeName  = requirement_record.stripeTitle
                student_record.studentPromotionDate = datetime.now().strftime(constants.fmtDateTime)
        elif not student_record.currentRankNum and student_record.currentStripeId:
            # get and set the belt/rank for the related stripe
            requirement_record_stmt = (
                select(Requirements)
                .where(Requirements.stripeId == student_record.currentStripeId)
            )
            requirement_record = db_session.scalars(requirement_record_stmt).first()
            student_record.currentRankNum = requirement_record.beltId
            student_record.currentRankName = requirement_record.beltTitle
        elif student_record.currentRankNum and not student_record.currentStripeId:
            # get and set the initial stripe for the current belt/rank
            requirement_record_stmt = (
                select(Requirements)
                .where(Requirements.beltId == student_record.currentRankNum)
                .order_by(Requirements.stripeSeqNum)
            )
            requirement_record = db_session.scalars(requirement_record_stmt).first()
            student_record.currentStripeId = requirement_record.stripeId
            student_record.currentStripeName = requirement_record.stripeTitle

        if not student_record.studentPromotionDate:
            student_record.studentPromotionDate = datetime.now().strftime(constants.fmtDateTime)

        # print(f'CheckStudentRank :: Session state before: {db_session.is_modified(student_record)}')
        if db_session.is_modified(student_record):
            db_session.commit()
        # print(f'CheckStudentRank :: Session state after: {db_session.is_modified(student_record)}')

    except Exception as ex:
        print(f'Error: {str(ex)}')
        raise ex

# -----------------------------------------------------------------------------------
# ensure the promotion is being updated
# -----------------------------------------------------------------------------------
def IsDuplicatePromotion(studentData: Students, requestJson) -> bool:
    if studentData.currentRankNum is None:
        return False
    currentRankNum   = studentData.currentRankNum
    selectedBeltId   = int(requestJson['beltId'])
    currentStripeId  = studentData.currentStripeId
    selectedStripeId = int(requestJson['stripeId'])
    if studentData.studentPromotionDate is None:
        currentPromotionDate = datetime.fromisoformat("1900-01-01T00:00:00")
    else:
        currentPromotionDate = parse(studentData.studentPromotionDate, fuzzy=False).date()
        #currentPromotionDate = studentData.studentPromotionDate
    selectedPromotionDate = requestJson['promotionDate']
    if (   currentRankNum == selectedBeltId
       and currentStripeId == selectedStripeId
       and currentPromotionDate == selectedPromotionDate):
        return True

    return False

def UpdStudentPromotionRecords(
        student_record: Students,
        belt_id: int,
        stripe_id: int,
        promotion_date: datetime
):
    try:
        # update the student record from the new data
        if belt_id != student_record.currentRankNum:
            promotion_type = 'Belt'
        else:
            promotion_type = 'Stripe'

        requirement_record_stmt = (select(Requirements)
                                   .where(Requirements.beltId == belt_id, Requirements.stripeId == stripe_id)
                                   )
        requirement_record = db_session.scalars(requirement_record_stmt).first()
        student_record.currentRankNum = requirement_record.beltId
        student_record.currentRankName = requirement_record.beltTitle
        student_record.currentStripeId = requirement_record.stripeId
        student_record.currentStripeName = requirement_record.stripeTitle
        student_record.studentPromotionDate = promotion_date.strftime(constants.fmtDateTime)
        db_session.commit()
        print(f'{constants.consoleRed}Student   record status: {db_session.is_modified(student_record)}')

        promotion_record = Promotions()
        promotion_record.badgeNumber      = student_record.badgeNumber
        promotion_record.beltId           = student_record.currentRankNum
        promotion_record.beltTitle        = student_record.currentRankName
        promotion_record.stripeId         = student_record.currentStripeId
        promotion_record.stripeTitle      = student_record.currentStripeName
        promotion_record.studentName      = student_record.firstName + ' ' + student_record.lastName
        promotion_record.promotionDate    = promotion_date.strftime(constants.fmtDateTime)
        promotion_record.studentFirstName = student_record.firstName
        promotion_record.studentLastName  = student_record.lastName
        promotion_record.comments         = "Promotion"
        promotion_record.promotionType    = promotion_type
        promotion_record.createDateTime   = datetime.now().strftime(constants.fmtDateTime)
        db_session.add(promotion_record)
        db_session.commit()
    except Exception as ex:
        print(f'{constants.consoleRed}Student   record status: {db_session.is_modified(student_record)}')
        print(f'{constants.consoleRed}Promotion record status: {db_session.is_modified(student_record)}')
        print(f'Error: {str(ex)}')
        raise ex

def GetNextPromotionDetails(student_record: Students):
    try:
        next_promotion_record = NextPromotion()

        # new students don't always have a rank, check for that
        CheckStudentRank(student_record)

        # belts are static, same list every time
        next_promotion_record.belt_records = db_session.scalars(select(Belts)).all()

        # fetch the requirement record for the current student rank
        current_requirement_record = (
            db_session.scalars(select(Requirements).where(Requirements.stripeId == student_record.currentStripeId))
            .first()
        )
        next_promotion_record.current_requirement_record = current_requirement_record

        # get requirement record for the next promotion,
        next_requirement_stmt = (select(Requirements)
                                 .where(Requirements.requirementId > current_requirement_record.requirementId)
                                 )
        next_requirement_record = (db_session.scalars(next_requirement_stmt).first())
        next_promotion_record.next_requirement_record = next_requirement_record

        # stripe records are dependent on the next requirement
        stripe_records = (db_session
                          .scalars(select(Requirements)
                                   .where(Requirements.beltId == next_requirement_record.beltId)
                                   .order_by(Requirements.stripeSeqNum))
                          .all())
        next_promotion_record.stripe_records = stripe_records

        # get the latest promotion dates
        next_promotion_record.last_belt_promotion_date    = GetLastBeltPromotionDate(student_record)
        next_promotion_record.last_stripe_promotion_date  = GetLastStripePromotionDate(student_record)


        # populate the attendance counts
        attendance_total_stmt = (select(func.count())
                                 .select_from(Attendance)
                                 .where(Attendance.badgeNumber == student_record.badgeNumber))
        next_promotion_record.attendance_count_total = db_session.scalar(attendance_total_stmt)

        attendance_since_belt_stmt = (select(func.count())
                                      .select_from(Attendance)
                                      .where(Attendance.badgeNumber == student_record.badgeNumber)
                                      .where(Attendance.checkinDateTime >=  next_promotion_record.last_belt_promotion_date)
                                      )
        #print(f'attendance_since_belt_stmt\n{attendance_since_belt_stmt.compile(compile_kwargs={"literal_binds": True})}')
        next_promotion_record.attendance_count_since_belt = db_session.scalar(attendance_since_belt_stmt)

        attendance_since_stripe_stmt = (select(func.count())
                                      .select_from(Attendance)
                                      .where(Attendance.badgeNumber == student_record.badgeNumber)
                                      .where(Attendance.checkinDateTime >=  next_promotion_record.last_stripe_promotion_date)
                                      )
        next_promotion_record.attendance_count_since_stripe = db_session.scalar(attendance_since_stripe_stmt)

        next_promotion_record.classes_until_from_total  = next_requirement_record.requiredClasses - next_promotion_record.attendance_count_total
        next_promotion_record.classes_until_from_belt   = next_requirement_record.classesCount    - next_promotion_record.attendance_count_since_belt
        next_promotion_record.classes_until_from_stripe = next_requirement_record.classesCount    - next_promotion_record.attendance_count_since_stripe

        count_values = [
            next_promotion_record.classes_until_from_total,
            next_promotion_record.classes_until_from_belt,
            next_promotion_record.classes_until_from_stripe
        ]
        result = min(x for x in count_values if x >= 0)
        # result = min(count_values)

        # only the last promotion date counts towards the next promotion
        last_promotion_record = (
            db_session.scalars(select(Promotions)
                               .where(Promotions.badgeNumber == student_record.badgeNumber)
                               .order_by(Promotions.promotionDate.desc()))
            .first()
        )


        if not last_promotion_record:
            last_promotion_date = student_record.createDateTime
        else:
            last_promotion_date = student_record.studentPromotionDate
        attendance_since_last_stmt = (select(func.count())
                                      .select_from(Attendance)
                                      .where(Attendance.badgeNumber == student_record.badgeNumber)
                                      .where(Attendance.checkinDateTime >= last_promotion_date)
                                      )
        attendance_since_last_count = db_session.scalar(attendance_since_last_stmt)


        result = next_requirement_record.classesCount - attendance_since_last_count
        #if next_requirement_record.classesCount >

        if result > 0:
            promotion_message = f'{result} classes until eligible for {next_requirement_record.beltTitle} with {next_requirement_record.stripeTitle}'
        else:
            promotion_message = f'You are eligible for {next_requirement_record.beltTitle} with {next_requirement_record.stripeTitle}'



        next_promotion_record.promotion_message = promotion_message
        return next_promotion_record
    except Exception as ex:
        traceback.print_exc()
        print(f'Error: {str(ex)}')
        raise ex

def GetLastBeltPromotionDate(student_record: Students):
    last_promotion_stmt = ((select(Promotions)
                            .where(Promotions.badgeNumber == student_record.badgeNumber)
                            .where(Promotions.promotionType == 'Belt'))
                           .order_by(Promotions.promotionDate.desc()))
    last_promotion = (db_session.scalars(last_promotion_stmt).first())
    if last_promotion:
        return parse(last_promotion.promotionDate, fuzzy=False)
    else:
        return parse(student_record.createDateTime, fuzzy=False)

def GetLastStripePromotionDate(student_record: Students):
    last_promotion_stmt = ((select(Promotions)
                            .where(Promotions.badgeNumber == student_record.badgeNumber)
                            .where(Promotions.promotionType == 'Stripe'))
                           .order_by(Promotions.promotionDate.desc()))
    last_promotion = (db_session.scalars(last_promotion_stmt).first())
    if last_promotion:
        return parse(last_promotion.promotionDate, fuzzy=False)
    else:
        return parse(student_record.createDateTime, fuzzy=False)
