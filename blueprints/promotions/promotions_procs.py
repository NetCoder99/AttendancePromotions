from flask import render_template
from flask_htmx import make_response
from sqlalchemy import select, func
from datetime import datetime

from blueprints.promotions.queries import GetNextPromotion
from models import Students, Requirements, Attendance, Belts, Promotions
from sqlite.sqlite_alchemy import getAlchemySession

db_session = getAlchemySession()

def BuildStudentDetailsHtml(student_record: Students):
    student_list_stmt     = select(Students).where(Students.badgeNumber == student_record.badgeNumber)
    student_record        = db_session.scalars(student_list_stmt).all()[0]
    student_name = f'{student_record.firstName} {student_record.lastName}'

    if not student_record.currentRankNum:
        requirement_record = (db_session
                          .scalars(select(Requirements)
                                   .where(Requirements.beltId == 1)
                                   .order_by(Requirements.stripeSeqNum))
                          .all())[0]
        student_record.currentRankNum     = requirement_record.beltId
        student_record.currentRankName    = requirement_record.beltTitle
        student_record.currentStripeId    = requirement_record.stripeId
        student_record.currentStripeName  = requirement_record.stripeTitle

    student_details_html  = render_template('partials/student_details.html',
                                            badge_number=student_record.badgeNumber,
                                            student_name=student_name,
                                            student_rank=student_record.currentRankName,
                                            student_stripe=student_record.currentStripeName)
    return student_details_html

def BuildAttendanceDetailsHtml(student_record: Students):
    try:
        stripe_id              = student_record.currentStripeId
        requirement_list_stmt  = select(Requirements).where(Requirements.stripeId == stripe_id)
        requirement_record     = db_session.scalars(requirement_list_stmt).all()[0]
        total_classes_attended = db_session.scalar(select(func.count()).select_from(Attendance).where(Attendance.badgeNumber == student_record.badgeNumber))
        requirements_counts    = render_template(
            "partials/attendance_counts.html",
            total_classes_attended    = total_classes_attended,
            required_promotion_count = requirement_record.classesCount,
            required_total_count = requirement_record.requiredClasses
        )
        return requirements_counts
    except Exception as ex:
        print(f'Error: {str(ex)}')
        raise ex

def BuildPromotionsInputHtml(student_record: Students):
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
        stripe_records        = (db_session
                                 .scalars(select(Requirements)
                                          .where(Requirements.beltId == student_record.currentRankNum)
                                          .order_by(Requirements.stripeSeqNum))
                                 .all())
        current_requirement_record = (
            db_session.scalars(select(Requirements).where(Requirements.stripeId == student_record.currentStripeId))
            .first()
        )
        next_requirement_record = (
            db_session.scalars(select(Requirements)
                               .where(Requirements.requirementId > current_requirement_record.requirementId)
                               .order_by(Requirements.requirementId))
            .first()
        )

        # #next_promotion        = GetNextPromotion(student_record.badgeNumber)
        # if not next_promotion:
        #     current_requirement_record = (
        #         db_session.scalars(select(Requirements)
        #                            .where(Requirements.beltId == student_record.currentStripeId)
        #                            .order_by(Requirements.stripeSeqNum))
        #                          .first()
        #     )
        #     next_requirement_record = (
        #         db_session.scalars(select(Requirements)
        #                            .where(Requirements.requirementId > current_requirement_record.requirementId)
        #                            .order_by(Requirements.requirementId))
        #                            .first()
        #     )
        #

        # selection_stripes     = render_template('controls/selection_stripes.html',
        #                                         stripe_records=stripe_records,
        #                                         current_stripe_id=student_record.currentStripeId,
        #                                         next_stripe_id=next_promotion['stripeId'])

        student_promotions    = render_template('partials/student_promotions.html',
                                                belts_records     = belts_records,
                                                current_belt_id   = student_record.currentRankNum,
                                                stripe_records    = stripe_records,
                                                current_stripe_id = student_record.currentStripeId,
                                                next_stripe_id    = 181,
                                                initial_promotion_date=datetime.now().strftime("%Y-%m-%d"))
        return student_promotions
    except Exception as ex:
        print(f'Error: {str(ex)}')
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
