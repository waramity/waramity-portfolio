function submitComment(item_type, item_slug) {
  document.getElementById("submit-comment-button").classList.add("disabled");

  let comment = $("#comment-textarea").val();
  let prompt_children = $(".prompt-container").children();
  let prompts = {
    comment: comment,
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

  fetch(`/en/comment/${item_type}/${item_slug}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(prompts),
  }).then((res) => {
    res.json().then((data) => {
      if (data["status"] == 0) {
        removeErrorMessage();
        showErrorMessage(data["error_message"]);
        $("#submit-comment-button.disabled").toggleClass("disabled");
      } else {
        window.location.href = `${data["redirect_url"]}`;
      }
    });
  });
}
