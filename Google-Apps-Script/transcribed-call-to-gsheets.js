function doPost(e) {
  try{
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName("Sheet2");
    const range = sheet.getRange("E2:E100"); // The area where dropdowns will exist

    // Parse the JSON data sent from the Python script.
    const postData = JSON.parse(e.postData.contents);

    // Extract the data from the parsed JSON object.
    const toolCalls = JSON.stringify(postData.tool_calls); // Stringify the list for sheet compatibility
    const toolResults = JSON.stringify(postData.tool_call_results); // Stringify the list
    const summary = postData.summary;
    const name = postData.name;
    const phoneNumber = postData.phone_number;
    const leadIntent = postData.lead_intent;

    // 1. Define the Dropdown Rule
    const options = ['High', 'Medium', 'Low'];
    const rule = SpreadsheetApp.newDataValidation()
      .requireValueInList(options)
      .setAllowInvalid(false)
      .build();

    // 2. Clear existing rules to avoid duplicates, then set new ones
    // Note: This sets the rules for the whole column once
    const rules = [
      createRule(range, "High", "#00FF00"),   // Green
      createRule(range, "Medium", "#FFFF00"), // Yellow
      createRule(range, "Low", "#FF0000")     // Red
    ];
    sheet.setConditionalFormatRules(rules);

    // 3. Append the new row
    // name, phone, toolCalls, toolResults, leadIntent, summary
    sheet.appendRow([name, phoneNumber, toolCalls, toolResults, leadIntent, summary]);

    // 4. Apply the dropdown validation to the newly appended cell
    const lastRow = sheet.getLastRow();
    sheet.getRange(lastRow, 5).setDataValidation(rule);

    // Return a success response to the Python script.
    return ContentService
      .createTextOutput(JSON.stringify({ "status": "success", "message": "Row added." }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    // If an error occurs, return an error message for debugging.
    return ContentService
      .createTextOutput(JSON.stringify({ "status": "error", "message": error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Helper function to build a conditional formatting rule
 */
function createRule(range, value, color) {
  return SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo(value)
    .setBackground(color)
    .setRanges([range])
    .build();
}