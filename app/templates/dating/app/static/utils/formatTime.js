function formatTime(dtStr) {
  var dt = new Date(dtStr);
  var monthNames = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];

  var formattedDate =
    monthNames[dt.getMonth()] + " " + dt.getDate() + ", " + dt.getFullYear();

  return formattedDate;
}

function formatTimeDifference(date_str) {
  var date = new Date(date_str);
  var timeDiff = Math.abs(Date.now() - date.getTime());
  var diffMinutes = Math.ceil(timeDiff / (1000 * 60));
  var diffHours = Math.ceil(timeDiff / (1000 * 60 * 60));
  var diffDays = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
  var diffMonths = Math.ceil(timeDiff / (1000 * 60 * 60 * 24 * 30));

  if (diffMinutes < 60) {
    document.getElementById("last-updated").innerHTML =
      diffMinutes + " minutes ago";
  } else if (diffHours < 24) {
    document.getElementById("last-updated").innerHTML =
      diffHours + " hours ago";
  } else if (diffDays < 30) {
    document.getElementById("last-updated").innerHTML = diffDays + " days ago";
  } else {
    document.getElementById("last-updated").innerHTML =
      diffMonths + " months ago";
  }
}
