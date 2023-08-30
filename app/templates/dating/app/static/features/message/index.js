function showErrorMessage(error_message) {
  $('span[id="error-message"]').text("* " + error_message);
}

function removeErrorMessage() {
  $('span[id="error-message"]').text("");
}

function showMessage(message) {
  $('span[id="message"]').text("" + message);
}

function removeMessage() {
  $('span[id="message"]').text("");
}
