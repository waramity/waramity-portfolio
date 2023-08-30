let comment_template = document.querySelector("#comment-template");
let comments_section = document.querySelector("#comments");

async function likeComment(comment_slug, item_type, item_slug) {
  if ($(`#like-button-${comment_slug}`).hasClass("disabled")) {
    return;
  }
  $(`#like-button-${comment_slug}`).addClass("disabled");
  fetch(`/en/comment/${item_type}/${item_slug}/${comment_slug}/like`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  }).then((res) => {
    res.json().then((data) => {
      if (data["status"] == 0) {
        removeErrorMessage();
        showErrorMessage(data["error_message"]);
      }
      $(`#like-button-${comment_slug}`).removeClass("disabled");
    });
  });
}

async function toggleLikeButton(comment_slug, item_type, item_slug) {
  like_button = $(`#like-button-${comment_slug}`);
  like_amount = $(`#like-button-${comment_slug}`).find("span");
  like_icon = $(`#like-button-${comment_slug}`).find("i").get(0);

  $(like_icon).toggleClass("text-danger");
  if ($(`#like-button-${comment_slug} i.text-danger`).length) {
    likes = parseInt(like_amount.html()) + 1;
    like_amount.html(likes);
  } else {
    likes = parseInt(like_amount.html()) - 1;
    like_amount.html(likes);
  }
  if (like_icon.classList.contains("bi-heart-fill")) {
    like_icon.classList.remove("bi-heart-fill");
    like_icon.classList.add("bi-heart");
  } else {
    like_icon.classList.remove("bi-heart");
    like_icon.classList.add("bi-heart-fill");
  }

  await likeComment(comment_slug, item_type, item_slug);
}

function appendComment(comment, item_type, item_slug, user_slug) {
  let comment_template_clone = comment_template.content.cloneNode(true);

  comment_template_clone.querySelector(
    "#profile-name"
  ).innerHTML = `${comment["user"]["profile_name"]}`;

  comment_template_clone.querySelector(
    "#comment-likes"
  ).innerHTML = `${comment["total_engagement"]["likes"]}`;

  comment_template_clone.querySelector(
    "#profile-image"
  ).src = `${comment["user"]["image_url"]}`;

  if (user_slug == comment["user"]["slug"]) {
    comment_template_clone.querySelector(
      "#option-dropdown-list"
    ).innerHTML = `<li><a class="dropdown-item delete-button">Delete</a></li>`;
    comment_template_clone
      .querySelector("a.delete-button")
      .addEventListener("click", async () => {
        await deleteComment(`${comment["slug"]}`);
      });
  } else {
    comment_template_clone.querySelector("#options").innerHTML = ``;
  }

  if (comment["current_user_liked"]) {
    comment_template_clone.querySelector(".bi-heart").className =
      "bi bi-heart-fill text-danger me-2";
  }

  comment_template_clone.querySelector("#created-date").innerHTML = formatTime(
    comment["created_date"]
  );

  comment_template_clone
    .querySelector("#like-button")
    .addEventListener("click", async () => {
      await toggleLikeButton(`${comment["slug"]}`, item_type, item_slug);
    });

  comment_template_clone
    .querySelector("#like-button")
    .classList.add(`${comment["slug"]}`);

  comment_template_clone.querySelector(
    "#like-button"
  ).id = `like-button-${comment["slug"]}`;

  comment_template_clone.querySelector(
    "#comment"
  ).id = `comment-${comment["slug"]}`;

  comment_template_clone.querySelector(
    "#comment-text"
  ).innerHTML = prepareDescription(`${comment["comment"]}`);

  if (comment["prompts"].length != 0) {
    comment_template_clone.querySelector(
      ".swiper"
    ).innerHTML = `<div class="swiper-wrapper"></div>
      <div class="swiper-pagination"></div>
      <div class="swiper-button-next"></div>
      <div class="swiper-button-prev"></div>`;

    for (var i = 0; i < comment["prompts"].length; i++) {
      comment_template_clone.querySelector(
        ".swiper-wrapper"
      ).innerHTML += `<div class="swiper-slide"><img src="${comment["prompts"][i]["image_url"]}" class="w-100" /></div>`;
    }

    new Swiper(comment_template_clone.querySelector(".swiper"), {
      loop: true,
      navigation: {
        nextEl: `.swiper-button-next`,
        prevEl: `.swiper-button-prev`,
      },
      pagination: {
        el: ".swiper-pagination",
      },
    });
  }

  const profile_links = comment_template_clone.querySelectorAll(
    ".profile-link"
  );

  for (let i = 0; i < profile_links.length; i++) {
    const link = profile_links[i];
    link.setAttribute("href", `/th/profile/${comment["user"]["profile_name"]}`);
  }

  comments_section.appendChild(comment_template_clone.children[0]);
}

function createComments(comments, item_type, item_slug, user_slug) {
  for (var i = comments.length - 1; i >= 0; i--) {
    appendComment(comments[i], item_type, item_slug, user_slug);
  }
}

function showCommentMessage(message) {
  document.querySelector(
    "#comments"
  ).innerHTML = `<p class="my-5 text-center">${message}</p>`;
}

function getComments(item_type, item_slug, user_slug) {
  fetch(`/en/get-comments/${item_type}/${item_slug}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  }).then((res) => {
    res.json().then((data) => {
      if (data["status"] == 0) {
        removeErrorMessage();
        showErrorMessage(data["error_message"]);
      } else {
        if (data["message"] == null) {
          createComments(data["comments"], item_type, item_slug, user_slug);
        } else {
          showCommentMessage(data["message"]);
        }
      }
    });
  });
}

function removeComment(comment_slug) {
  $(`#comment-${comment_slug}`).remove();
}

async function deleteComment(comment_slug) {
  fetch(`/en/delete-comment/${comment_slug}`, {
    method: "POST",
    headers: { Accept: "application/json" },
  }).then((res) => {
    res.json().then((data) => {
      if (data["status"] == 0) {
        removeErrorMessage();
        showErrorMessage(data["error_message"]);
      } else {
        removeComment(comment_slug);
      }
    });
  });
}
