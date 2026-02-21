// This sends an Event to inngest when the google form is submitted.
function onSubmit(e) {
  var itemResponses = e.response.getItemResponses();
  var formData = {};

  // 1. Define your mapping: "Form Question Title": "Object Key"
  var fieldMap = {
    "Full name": "name",
    "Phone number": "phone",
    "Business Description": "story",
    "Service address (including estate/building name and any landmarks)": "service_address",
    "What type of place is this?": "place_type",
    "What plumbing service do you need?": "service_needed",
    "Please briefly describe the problem or work required": "problem",
    "When did this issue start?": "issue_start",
    "How urgent is this job?": "job_urgency",
    "Preferred date for visit": "preferred_date_for_visit",
    "Preferred time window for visit": "preferred_time_for_visit"
  };

  for (var i = 0; i < itemResponses.length; i++) {
    var question = itemResponses[i].getItem().getTitle();
    var answer = itemResponses[i].getResponse();

    // 3. If the question exists in our map, assign the answer to that key
    var mappedKey = fieldMap[question];
    if (mappedKey) {
      formData[mappedKey] = answer;
    }


  }

  // The Payload: Inngest expects an OBJECT for a single event via the /e/ endpoint
  // OR an ARRAY of objects. Most people send a single object.
  var eventPayload = {
    name: "google/form.submitted",
    data: formData
  };

  // YOUR ACTION REQUIRED: Replace 'YOUR_EVENT_KEY' with the key from Inngest Dashboard
  var inngestEventKey = "INNGEST_EVENT_KEY"; 
  var url = "https://inn.gs/e/" + inngestEventKey;

  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(eventPayload)
  };

  try {
    var response = UrlFetchApp.fetch(url, options);
    console.log("Event sent! Status: " + response.getResponseCode());
  } catch (err) {
    console.error("Error sending to Inngest: " + err.message);
  }
}