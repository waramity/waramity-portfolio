async function toggleFollowButton(profile_name) {
  var button = document.getElementById("follow-button");

  $("#follow-button").toggleClass("disabled");

  await followUser(profile_name);

  $("#follow-button.disabled").toggleClass("disabled");

  if (button.classList.contains("btn-primary")) {
    button.classList.remove("btn-primary");
    button.classList.add("btn-outline-primary");
    button.innerHTML = "Unfollow";
  } else {
    button.classList.remove("btn-outline-primary");
    button.classList.add("btn-primary");
    button.innerHTML = "Follow";
  }
}

async function followUser(profile_name) {
  let follow_json = {
    following_profile_name: `${profile_name}`,
  };
  fetch(`/en/follow`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(follow_json),
  }).then((res) => {
    res.json().then((data) => {
      if (data["status"] == 0) {
        removeErrorMessage();
        showErrorMessage(data["error_message"]);
      }
    });
  });
}
