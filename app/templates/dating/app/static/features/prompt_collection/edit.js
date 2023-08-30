async function submitEditPrompt(slug) {
  document.getElementById("submit-edit-button").classList.add("disabled");
  let topic = $("#topic-input").val();
  let description = $("#description-textarea").val();
  let model_name = $("#model-input").val();
  let prompt_children = $(".prompt-container").children();

  let prompts = {
    topic: topic,
    description: description,
    model_name: model_name,
    prompts: [],
  };

  prompt_children.each(function (i) {
    let prompt_json = {
      image_url: "",
      prompt: "",
      negative_prompt: "",
      steps: 0,
      sampler: "",
      cfg_scale: 0,
      seed: 0,
      size: "",
      model_hash: "",
    };

    prompt_json.image_url = prompt_children[i].querySelector(
      "#prompt-image"
    ).src;

    prompt_json.prompt = prompt_children[i].querySelector(
      "#prompt-input"
    ).value;

    prompt_json.negative_prompt = prompt_children[i].querySelector(
      "#negative-prompt-input"
    ).value;

    prompt_json.steps = prompt_children[i].querySelector("#steps-input").value;

    prompt_json.sampler = prompt_children[i].querySelector(
      "#sampler-input"
    ).value;

    prompt_json.cfg_scale = prompt_children[i].querySelector(
      "#cfg-scale-input"
    ).value;

    prompt_json.seed = prompt_children[i].querySelector("#seed-input").value;

    prompt_json.size = prompt_children[i].querySelector("#size-input").value;

    prompt_json.model_hash = prompt_children[i].querySelector(
      "#model-hash-input"
    ).value;

    prompts.prompts.push(prompt_json);
  });

  try {
    const response = await fetch(`/en/submit-edit-prompt/${slug}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prompts),
    });

    const data = await response.json();

    if (data["status"] === 0) {
      removeErrorMessage();
      showErrorMessage(data["error_message"]);
      $("#submit-edit-button.disabled").toggleClass("disabled");
    } else {
      window.location.href = `${data["redirect_url"]}`;
    }
  } catch (error) {
    console.error(error);
  }
}

function appendPromptItem(item) {
  var prompt_item_template = document.querySelector(
    "#prompt-item-dropzone-template"
  );
  let prompt_item_template_clone = prompt_item_template.content.cloneNode(true);

  prompt_item_template_clone.querySelector(
    "#prompt-image"
  ).src = `${item["image_url"]}`;

  prompt_item_template_clone.querySelector(
    "#prompt-input"
  ).value = `${item["prompt"]}`;

  prompt_item_template_clone.querySelector(
    "#negative-prompt-input"
  ).value = `${item["negative_prompt"]}`;

  prompt_item_template_clone.querySelector(
    "#sampler-input"
  ).value = `${item["sampler"]}`;

  prompt_item_template_clone.querySelector(
    "#steps-input"
  ).value = `${item["steps"]}`;

  prompt_item_template_clone.querySelector(
    "#seed-input"
  ).value = `${item["seed"]}`;

  prompt_item_template_clone.querySelector(
    "#size-input"
  ).value = `${item["size"]}`;

  prompt_item_template_clone.querySelector(
    "#cfg-scale-input"
  ).value = `${item["cfg_scale"]}`;

  prompt_item_template_clone.querySelector(
    "#model-hash-input"
  ).value = `${item["model_hash"]}`;

  const uuid = Math.random().toString(36).substring(2, 10);
  prompt_item_template_clone.querySelector(".row").id = `${uuid}`;

  prompt_item_template_clone
    .querySelector("#delete-button")
    .addEventListener("click", function () {
      const elementToDelete = document.getElementById(uuid);
      elementToDelete.parentNode.removeChild(elementToDelete);

      images -= 1;
    });

  prompt_container.appendChild(prompt_item_template_clone.children[0]);
}

function createPromptCollection(item) {
  $("#topic-input").val(item["topic"]);
  $("#description-textarea").val(item["description"]);
  $("#model-input").val(item["model_name"]);

  for (let i = 0; i < item["prompts"].length; i++) {
    appendPromptItem(item["prompts"][i]);
  }
}

async function getPromptCollectionInfo(profile_name, slug) {
  const res = await fetch(
    `/en/get-prompt-collection/${profile_name}/${slug}/edit`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
    }
  );
  const data = await res.json();
  createPromptCollection(data["prompt_collection"]);

  images = data["prompt_collection"]["prompts"].length;
}
