import sys
from sqlalchemy import text
from sqlite.sqlite_alchemy import getAlchemySession

db_session = getAlchemySession()

def GetStripeNamesByRank():
    return '''
        select s.rankNum, 
               r.beltTitle,
               s.stripeId,
               s.stripeName
        from   stripes  s
        join   belts    r
          on   s.rankNum = r.beltId
        where  s.rankNum = :rankNum
        order  by s.rankNum, s.seqNum
    '''

def GetPromotionHistoryStmt():
    return '''
        select p.promotionId,
           p.badgeNumber,
           p.beltId,
           p.beltTitle,
           p.stripeId,
           p.stripeTitle,
           p.studentName,
           p.promotionDate,
           date(p.promotionDate) as promotionDateStr
        from   promotions  p
        where  p.badgeNumber = :badgeNumber
        order  by p.promotionId desc;
    '''

def GetNextPromotion(badge_number):
    try:
        query  = text(GetNextPromotionStmt())
        result = db_session.execute(query, {'badgeNumber' : badge_number})
        for row in result.mappings():
            return row
        raise Exception('No rows found!')
    except Exception as ex:
        print(f'{str(ex)}', file=sys.stderr)

def GetNextPromotionStmt():
    return '''
            with cte_current_requirement_id as
            (
                select r1.promotionSeqNum
                from   students s1
                join   requirements r1
                  on   s1.currentRankNum  = r1.beltId
                  and  s1.currentStripeId = r1.stripeId
                where  s1.badgeNumber = :badgeNumber
            )
            select requirementId,
                beltId,
                beltTitle,
                stripeId,
                stripeTitle,
                stripeSeqNum,
                classesCount,
                requiredClasses,
                promotionSeqNum,
                createDateTime,
                updateDateTime
            from   requirements r2
            where  r2.promotionSeqNum > (select promotionSeqNum from cte_current_requirement_id)
            order  by r2.promotionSeqNum asc
            limit  1
        '''

def GetNextPromotionStmtV2():
    return '''
        select r1.requirementId,
            r1.beltId,
            r1.beltTitle,
            r1.stripeId,
            r1.stripeTitle,
            r1.stripeSeqNum,
            r1.classesCount,
            r1.requiredClasses,
            r1.promotionSeqNum,
            r1.createDateTime,
            r1.updateDateTime
        from   requirements r1 
        where  r1.requirementId > 
        (
            select r.requirementId
            from   requirements r 
            order  by r.beltId, stripeSeqNum
        )
        limit 1  
        '''

def GetStudentRecordsStmtByBadge():
    return '''
        with cte_default_image as (
          select a.imageId,
                 a.imageName,
                 a.imageType,
                 a.imageBase64
          from  assets a
          where a.imageId = 428
        )    
        SELECT s.badgeNumber,
               s.firstName,
               s.lastName,
               s.namePrefix,
               s.email,
               s.address,
               s.address2,
               s.city,
               s.country,
               s.state,
               s.zip,
               s.birthDate,
               s.phoneHome,
               s.phoneMobile,
               s.status,
               s.memberSince,
               s.gender,
               s.ethnicity,
               s.middleName,
               s.currentRankNum,
               s.currentRankName,
               s.currentStripeId,
               s.currentStripeName,
               s.studentPromotionDate,
               b.beltTitle,
               case when s.studentImageBase64 is not null
                    then s.studentImageBase64 
                    else (select imageBase64 from cte_default_image)
               end as studentImageBase64,   
               case when s.studentImageBase64 is not null
                    then s.studentImageName 
                    else (select imageName from cte_default_image)
               end as studentImageName,   
               case when s.studentImageBase64 is not null
                    then s.studentImageType 
                    else (select imageType from cte_default_image)
               end as studentImageType   
        from students  s
        left join belts b
            on s.currentRankNum = b.beltId
        where  s.badgeNumber    = :badgeNumber    
    '''

# def UpdateStudentRankStmt():
#     return '''
#         update students
#         set    currentRankNum       = :currentRankNum,
#                currentRankName      = :currentRankName,
#                currentStripeId      = :currentStripeId,
#                currentStripeName    = :currentStripeName,
#                studentPromotionDate = :studentPromotionDate
#         where  badgeNumber       = :badgeNumber
#     '''

def InsertPromotionsRankStmt():
    return '''
        INSERT INTO promotions (
           badgeNumber,
           beltId,
           beltTitle,
           stripeId,
           stripeTitle,
           studentFirstName,
           studentLastName,
           promotionDate,
           comments
        )
        VALUES (
           :badgeNumber,
           :beltId,
           :beltTitle,
           :stripeId,
           :stripeTitle,
           :studentFirstName,
           :studentLastName,
           :promotionDate,
           :comments
        );
    '''

def GetInsertPromotionDict(studentData: dict, updStudentDict: dict):
    return {
        'badgeNumber': studentData[0]['badgeNumber'],
        'beltId':      updStudentDict['currentRankNum'],
        'beltTitle':   updStudentDict['currentRankName'],
        'stripeId':    updStudentDict['currentStripeId'],
        'stripeTitle': updStudentDict['currentStripeName'],
        'studentFirstName': studentData[0]['firstName'],
        'studentLastName' : studentData[0]['lastName'],
        'promotionDate'   : updStudentDict['studentPromotionDate'],
        'comments'        : updStudentDict['comments']
    }

def DeleteStudentPromotionStmt():
    return '''
        delete from promotions 
        where  promotionId = :promotionId
    '''