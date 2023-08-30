const copy_button = document.querySelector("#copy-prompt-button");
document.addEventListener("click", () => {
  if (!copy_button.contains(event.target)) {
    copy_button.classList.remove("fw-bold");
    copy_button.classList.replace("btn-primary", "btn-outline-primary");
    copy_button.textContent = "COPY";
  }
});

$(document).ready(function () {
  $("#prompt-input").on("keyup", function (event) {
    if (event.keyCode === 13) {
      var prompt = $(this).val().trim();
      if (prompt !== "") {
        addPrompt(prompt);
        $(this).val("");
      }
    }
  });
});

function copyPromptInput(prompt_input_id) {
  let prompt_input = document.getElementById(prompt_input_id);
  let prompt_texts = $("div#prompt-container span.badge");
  let copied_prompt_text = "";
  prompt_texts.each(function (index) {
    let prompt_text = $(this)
      .clone()
      .children(".ms-2.text-secondary")
      .remove()
      .end()
      .text()
      .trim();
    if (index !== prompt_texts.length - 1) {
      copied_prompt_text += prompt_text + ",";
    } else {
      copied_prompt_text += prompt_text;
    }
  });

  copy_button.classList.add("fw-bold");
  copy_button.classList.replace("btn-outline-primary", "btn-primary");
  copy_button.textContent = "COPIED!";

  navigator.clipboard.writeText(copied_prompt_text);
}

function clearPromptInput(prompt_input_id) {
  let prompt_input = document.getElementById(prompt_input_id);
  prompt_input.innerHTML = "";

  $("i.bi-trash.text-danger")
    .removeClass("bi-trash text-danger")
    .addClass("bi-plus text-primary");

  $("#topic-nav-list")
    .find("span")
    .each(function () {
      $(this).html(" ");
    });

  $("#category-nav")
    .find("span")
    .each(function () {
      $(this).html("");
    });
}

function addPrompt(prompt, prompt_id, category_slug) {
  if (prompt_id == null) {
    $(
      `<h5 role="button" class="me-1"><span class="badge bg-light text-dark ">` +
        prompt +
        `<span class='ms-2 text-secondary'>&times;</span>` +
        `</span>,</h5>`
    )
      .appendTo("#prompt-container")
      .on("click", function () {
        $(this).remove();
      });
  } else {
    $(
      `<h5 role="button" class="me-1 ${prompt_id}"><span class="badge bg-light text-dark ">` +
        prompt +
        `<span class='ms-2 text-secondary'>&times;</span>` +
        `</span>,</h5>`
    )
      .appendTo("#prompt-container")
      .on("click", function () {
        $(this).remove();

        let prompt_element = $(`#${prompt_id}`);
        if (prompt_element != null) {
          prompt_element
            .find("i")
            .removeClass("bi-trash text-danger")
            .addClass("bi-plus text-primary");
        }

        removeCategoryCount(category_slug);
      });
  }
}

function likePromptCollection() {
  if ($("#heart-button").hasClass("disabled")) {
    return;
  }
  $("#heart-button").addClass("disabled");
  fetch(`/en/prompt-builder/${profile_name}/${slug}/like`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  }).then((res) => {
    res.json().then((data) => {
      if (data["status"] == 0) {
        removeErrorMessage();
        showErrorMessage(data["error_message"]);
      } else {
        toggleHeartButton();
      }

      $("#heart-button").removeClass("disabled");
    });
  });
}

function toggleHeartButton() {
  $(".bi-heart-fill").toggleClass("text-danger");
  if ($(".bi-heart-fill.text-danger").length) {
    hearts = parseInt($("#heart-amount").html()) + 1;
    $("#heart-amount").html(hearts);
  } else {
    hearts = parseInt($("#heart-amount").html()) - 1;
    $("#heart-amount").html(hearts);
  }
}

function toggleBookmarkButton() {
  $(".bi-bookmark-fill").toggleClass("text-warning");
}

function bookmarkPromptBuilder() {
  if ($("#bookmark-button").hasClass("disabled")) {
    return;
  }
  $("#bookmark-button").addClass("disabled");
  fetch(`/en/prompt-builder/${profile_name}/${slug}/bookmark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  }).then((res) => {
    res.json().then((data) => {
      if (data["status"] == 0) {
        removeErrorMessage();
        showErrorMessage(data["error_message"]);
      } else {
        toggleBookmarkButton();
      }

      $("#bookmark-button").removeClass("disabled");
    });
  });
}

function removeMain(parent) {
  const childToRemove = parent.children[0];
  childToRemove.remove();
}

async function getCategories(slug) {
  const response = await fetch(`/en/get-categories/public/${slug}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  const data = await response.json();
  return data;
}

function removeCategoryItems(category_nav) {
  category_nav.innerHTML = "";
}

function createCategoryItems(categories) {
  for (var i = 0; i < categories.length; i++) {
    appendCategoryNav(categories[i]);
  }
}

function appendCategoryNav(category) {
  let category_nav_item_template_clone = category_nav_item_template.content.cloneNode(
    true
  );

  category_nav_item_template_clone.querySelector(
    "#category-nav-item"
  ).innerHTML = `${category["name"]}<span class="${category["slug"]}"></span>`;

  category_nav_item_template_clone
    .querySelector("#category-nav-item")
    .addEventListener("click", toggleCategory(category));

  category_nav_item_template_clone.querySelector(
    "#category-nav-item"
  ).id = `${category["slug"]}`;

  category_nav.insertAdjacentElement(
    "beforeend",
    category_nav_item_template_clone.children[0]
  );
}

function toggleCategory(category) {
  return function (event) {
    event.preventDefault();
    $(".category-nav-item.active").toggleClass("active");
    $(".category-nav-item.disabled").toggleClass("disabled");
    this.classList.add("active");
    this.classList.add("disabled");
    showCategoryInfo(category["name"], category["slug"]);

    getPrompts(category["slug"])
      .then((res) => {
        if (res["status"] == 0) {
          removeErrorMessage();
          showErrorMessage(res["error_message"]);
        } else if (res["prompts"].length) {
          removeErrorMessage();
          removeMessage();
          createPromptItems(category["slug"], res["prompts"]);
        } else {
          removePromptKeywords();
          showMessage("หัวข้อนี้ยังไม่มีข้อมูล");
        }
      })
      .catch((error) => {
        removeErrorMessage();
        showErrorMessage(error);
      });

    removePromptKeywords();
  };
}

async function getPrompts(category_slug) {
  try {
    const response = await fetch(
      `/en/get-prompts-prompt-builder/${slug}/${category_slug}`,
      {
        method: "GET",
        headers: { Accept: "application/json" },
      }
    );
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(error);
  }
}

function showCategoryInfo(category_name, category_slug) {
  $("#category-name-header").html(category_name);
  $("#category-name").html(
    `<h2 id="category-name-header" class="me-2">${category_name}</h2>`
  );
}

function removeCategoryInputValue() {
  $('input[id="category-input"]').val("");
}

function removePromptKeywords() {
  $('div[id="prompt-keywords"]').html(``);
}

function createPromptItems(category_slug, prompts) {
  $('div[id="prompt-keywords"]').html(`
      <div class="row" id="prompt-keywords-list">`);
  for (var i = 0; i < prompts.length; i++) {
    appendPromptItem(category_slug, prompts[i]);
  }
}

function appendPromptItem(category_slug, prompt) {
  let prompt_item_template_clone = prompt_item_template.content.cloneNode(true);

  prompt_item_template_clone.querySelector(
    "#prompt-image"
  ).src = `${prompt["image_url"]}`;

  prompt_item_template_clone.querySelector(
    "#prompt-name"
  ).innerHTML = `${prompt["name"]}`;

  let existing_prompt = $(`.${prompt["slug"]}`);
  if (existing_prompt.length > 0) {
    prompt_item_template_clone.querySelector(
      "#prompt-icon-button"
    ).innerHTML = `<i class="bi bi-trash text-danger"></i>`;
  } else {
    prompt_item_template_clone.querySelector(
      "#prompt-icon-button"
    ).innerHTML = `<i class="bi bi-plus text-primary"></i>`;
  }

  let isToggle = false;
  prompt_item_template_clone
    .querySelector(".card-body")
    .addEventListener("click", function () {
      togglePrompt(category_slug, prompt, isToggle, this);
    });

  prompt_item_template_clone.querySelector(
    "#prompt-item"
  ).id = `${prompt["slug"]}`;

  prompt_keywords
    .querySelector("#prompt-keywords-list")
    .insertBefore(
      prompt_item_template_clone.children[0],
      prompt_keywords.querySelector("#prompt-keywords-list").lastElementChild
    );
}

function togglePrompt(category_slug, prompt, isToggle, parent_element) {
  let existing_prompt = $(`.${prompt["slug"]}`);
  if (existing_prompt.length > 0) {
    isToggle = false;
  } else {
    isToggle = !isToggle;
  }

  parent_element.querySelector("#prompt-icon-button").innerHTML = isToggle
    ? `<i class="bi bi-trash text-danger"></i>`
    : `<i class="bi bi-plus text-primary"></i>`;

  if (isToggle) {
    addPrompt(prompt["name"], prompt["slug"], category_slug);
    addCategoryCount(category_slug);
  } else {
    removePrompt(prompt["slug"]);
    removeCategoryCount(category_slug);
  }
  return isToggle;
}

function removePrompt(prompt_id, topic_slug) {
  if (topic_slug == null) {
    $(`.${prompt_id}`).remove();
  } else {
    $(`.${prompt_id}.${topic_slug}`).remove();
  }
}

function addCategoryCount(category_slug) {
  const category_element = document.querySelector(`span.${category_slug}`);
  const count_text = category_element.textContent;

  let count = 1;
  if (count_text !== "") {
    count = parseInt(count_text.replace(/\D/g, "")) + 1;
  }

  category_element.textContent = ` (${count})`;
}

function removeCategoryCount(category_slug) {
  const category_element = document.querySelector(`span.${category_slug}`);
  const count_text = category_element.textContent;

  let count = 1;
  if (count_text !== "") {
    count = parseInt(count_text.replace(/\D/g, "")) - 1;
  }

  if (count != 0) {
    category_element.textContent = ` (${count})`;
  } else {
    category_element.textContent = ``;
  }
}
