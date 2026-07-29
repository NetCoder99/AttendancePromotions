
$(document).ready(function() {
    console.log("Document Checkin ready");

    startDateTimerInterval();

    $('#checkinTimer5').addClass("hidden");
    $('#checkinTimer4').addClass("hidden");
    $('#checkinTimer3').addClass("hidden");
    $('#checkinTimer2').addClass("hidden");
    $('#checkinTimer1').addClass("hidden");
    $('#checkinMessage2').addClass("removed");
    $('#checkinMessage3').addClass("removed");

    $('#badgeNumber').keydown(function(event) {
        console.log("badgeNumber keydown");
        if (event.which === 13) {
          event.preventDefault();
          processCheckinAction(event);
          console.log("Enter key pressed, default action prevented.");
        }
    });
    // manage confirmation dialog display
    $(".open-button").on("click", function() {
        showRankConfirmation(null);
    });
    $(".close-button, .popup-overlay").on("click", function(event) {
        if (event.target === this || $(event.target).hasClass("close-button")) {
            $(".popup-overlay").hide();
            startDateTimerInterval();
        }
    });
})
// ----------------------------------------------------------------------------------
document.getElementById('slctStudentBelt').addEventListener('change', function(event) {
    var rankNum = event.target.value;
    console.log("Checkin belt selected value is: " + rankNum);
    updateStripeDropdownCheckin(rankNum);
});

// -------------------------------------------------------------------------------
function showRankConfirmation(received_data) {
    console.log(`showRankConfirmation: ${JSON.stringify(received_data)}`);
    $('#hdnBadgeNumber').val(received_data.badgeNumber);

    stopDateTimerInterval();
    $('#slctStudentBelt').val(1);
    updateStripeDropdownCheckin(1);
    $(".popup-overlay").show(); // Use .toggle() for a simple show/hide switch
}

function updateStripeDropdownCheckin(rankNum) {
    const dataToSend = {'rankNum':rankNum};
    $.ajax({
      url: '/get_stripe_names',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(dataToSend),
      dataType: 'text',
      success: function(response) {
        processSelectRankResponseCheckin(response);
      },
      error: function(xhr, status, error) {
        console.error('Error:', error);
      }
    });
}
function processSelectRankResponseCheckin(stripeNameRecords) {
    const stripeNamesArray = JSON.parse(stripeNameRecords);
    console.log(`processSelectRankResponseCheckin was invoked: ${stripeNamesArray}`);
    $('#slctStudentStripe').empty();
    for (let i = 0; i < stripeNamesArray.length; i++) {
        console.log(stripeNamesArray[i]);
        $('#slctStudentStripe').append(`<option value=${stripeNamesArray[i].stripeId}>${stripeNamesArray[i].stripeName}</option>`);
    }
}

// -------------------------------------------------------------------------------
let dateTimerInterval;
function startDateTimerInterval() {
    if (!dateTimerInterval) {
        dateTimerInterval = setInterval(function() {
            $('#currentDateTime').text(getDisplayDate());
            $('#badgeNumber').focus();
        }, 1000);
    }
}
function stopDateTimerInterval() {
    clearInterval(dateTimerInterval);
    dateTimerInterval = null
}
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
function getDisplayDate(inpDate = new Date()) {
    const date = inpDate.toLocaleDateString();
    const time = inpDate.toLocaleTimeString();
    const day  = inpDate.toLocaleDateString('en-us',{ weekday: 'long' });
    return `${day} ${date} ${time}`;
}


// -------------------------------------------------------------------------------
function processCheckinAction(event) {
    $('#badgeNumber').prop('disabled', true);
    $('#checkinTimer5').removeClass("hidden");
    $('#checkinTimer4').removeClass("hidden");
    $('#checkinTimer3').removeClass("hidden");
    $('#checkinTimer2').removeClass("hidden");
    $('#checkinTimer1').removeClass("hidden");

    const badgeNumber = $('#badgeNumber').val();
    console.log(`badgeNumber: ${badgeNumber}`);
    $.post("/checkin", {"badgeNumber": badgeNumber}, function(response) {
        processCheckinResponse(response);
    });
}

// -------------------------------------------------------------------------------
function processCheckinResponse(response) {
    try {
        console.log(`processCheckinResponse: ${JSON.stringify(response)}`);

        if (response.received_data.needsRankConfirmation == 'Y') {
            showRankConfirmation(response.received_data);
        }

        $('#badgeNumber').val(null);
        $('#checkinMessage1').html(response.message);
        $('#checkinMessage1').removeClass("text-success");
        $('#checkinMessage1').removeClass("text-danger");
        if (response.status == 'error') {
            $('#checkinMessage1').addClass("text-danger");
            $('#checkinMessage2').addClass("removed");
            $('#checkinMessage3').addClass("removed");
        }
        else {
            let className = response.classData.classDisplayTitle;
            $('#checkinMessage1').html(`${className}`);
            $('#checkinMessage1').addClass("text-success");
            //$('#checkinMessage2').removeClass("removed");
            //$('#checkinMessage3').removeClass("removed");
        }
    }
    catch (error) {
        $('#checkinMessage1').html(error.message);
        $('#checkinMessage1').addClass("text-danger");
        $('#checkinMessage2').addClass("removed");
        $('#checkinMessage3').addClass("removed");
    } finally {
        let count = 5;
        const intervalID = setInterval(() => {
          console.log(`Tick: ${count}`);
          $('#checkinTimer'+count).addClass("hidden");
          count--;
          checkinTimer5
        }, 1000);

        setTimeout(() => {
          clearInterval(intervalID);
          console.log("Interval stopped.");
        }, 6000);

        setTimeout(() => {
          resetCheckinScreen();
        }, 6000);
    }
}

// -------------------------------------------------------------------------------
function resetCheckinScreen(response) {
    $('#badgeNumber').prop('disabled', false);
    $('#checkinMessage1').html("Waiting ...")
    $('#checkinMessage1').removeClass("text-success");
    $('#checkinMessage1').removeClass("text-danger");
    $('#checkinMessage2').addClass("removed");
    $('#checkinMessage3').addClass("removed");
}

// -------------------------------------------------------------------------------
$("#btnSaveStudentRankDialog").on("click", function(event) {
//    const badgeNumber    = $('#badgeNumber').val();
//    const selectedRank   = $('#slctStudentBelt').val();
//    const selectedStripe = $('#slctStudentStripe').val();
//$('#hdnBadgeNumber').val
    var now = new Date();
    const badgeNumber        = $('#hdnBadgeNumber').val();
    const selectedBeltId     = $("#slctStudentBelt").val();
    const selectedStripeId   = $("#slctStudentStripe").val();
    const selectedBeltName   = $("#slctStudentBelt option:selected").text();
    const selectedStripeName = $("#slctStudentStripe option:selected").text();

    const dataToSend = {
        'badgeNumber'   : badgeNumber,
        'beltId'        : selectedBeltId,
        'beltTitle'     : selectedBeltName,
        'stripeId'      : selectedStripeId,
        'stripeTitle'   : selectedStripeName,
        'studentName'   : null,
        'promotionDate' : now.toLocaleString().replace(/,/g, '')
    };

    console.log(`btnSaveStudentRankDialog: ${selectedBeltId} `);
    event.preventDefault();
    $.ajax({
      url: '/upd_student_rank',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(dataToSend),
      dataType: 'text',
      success: function(response) {
        console.log("Success:", response);
      },
      error: function(xhr, status, error) {
        console.error('Error:', error);
      }
    });

    $(".popup-overlay").hide();
    startDateTimerInterval();
});

$("#btnCancelStudentRankDialog").on("click", function(event) {
    console.log(`btnCancelStudentRankDialog`);
    event.preventDefault();
    $(".popup-overlay").hide();
    startDateTimerInterval();
});
