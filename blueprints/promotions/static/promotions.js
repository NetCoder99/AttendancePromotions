$(document).ready(function() {
    console.log("Promotions document ready");
//    htmx.logger = function(elt, event, data) {
//      if (console) {
//        console.log(`Event: ${event}`, elt, data);
//      }
//    };
})


document.body.addEventListener("resetResponseLabel", function (evt) {
    setTimeout(() => {
        $('#lblPromotionSaveResponse').html("Awaiting input ...");
    }, 4000);
});

function delPromotionRecord(promotionId){
    console.log(`delPromotionRecord was invoked: ${promotionId}`);
    const badgeNumber        = $('#hdnBadgeNumber').val();
    $.ajax({
      url: '/del_promotion_record',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({'promotionId' : promotionId, 'badgeNumber': badgeNumber}),
      dataType: 'text',
      success: function(response) {
        processAttendanceDeletion(response);
      },
      error: function(xhr, status, error) {
        console.error('Error:', error);
      }
    });
}

function processAttendanceDeletion(response){
    console.log(`processAttendanceDeletion was invoked: ${response}`);
    responseJson = JSON.parse(response);

    const lblPromotionSaveResponse2     = document.getElementById('lblPromotionSaveResponse')
    lblPromotionSaveResponse2.innerHTML = responseJson.message;
    displayPromotionsHistory(responseJson.promotionHistory);
    setTimeout(() => {
        $('#lblPromotionSaveResponse').html("Awaiting input ...");
    }, 4000);

}

function displayPromotionsHistory(promotionHistory) {
    console.log("displayPromotionsHistory");
    //promotionHistory = JSON.parse(response);
    const tbodyStudentPromotions = $('#tblStudentPromotions tbody');
    tbodyStudentPromotions.empty();
    //setBeltSelectionDropdowns(promotionHistory);
    for (let i = 0; i < promotionHistory.length; i++) {
        const inpPromotionDate = document.createElement('input');
        inpPromotionDate.type = 'date';
        inpPromotionDate.id = 'dynamic-date';
        inpPromotionDate.name = 'appointment-date';
        const tdPromotionDate = document.createElement('td')
        tdPromotionDate.appendChild(inpPromotionDate);
        const buttonId = `save_promotion_date_${promotionHistory[i].promotionId}`
        var newRow = `<tr>
                          <td>${promotionHistory[i].beltTitle}</td>
                          <td>${promotionHistory[i].stripeTitle}</td>
                          <td>
                            <input type="date" id="promotion-date-inp-${promotionHistory[i].promotionId}" name="promotion-date-inp-${promotionHistory[i].promotionId}" value=${promotionHistory[i].promotionDate} >
                          </td>
                          <td>
                            <button type  = "button"
                                    id    = "save-${buttonId}"
                                    class = "btn btn-sm btn-success"
                                    onclick = "savePromotionDate(${promotionHistory[i].promotionId})">
                                Save
                            </button>
                            <button type  = "button"
                                    id    = "del-${buttonId}"
                                    class = "btn btn-sm btn-success"
                                    onclick = "delPromotionRecord(${promotionHistory[i].promotionId})">
                                Del
                            </button>
                          </td>
                          <td>
                            <label id="promotion-response_${promotionHistory[i].promotionId}"></label>
                          </td>
                      </tr>`;
        tbodyStudentPromotions.append(newRow);
    }
}
