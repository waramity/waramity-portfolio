const MAX_IMAGES = 6; // maximum number of images to upload
let images = 0;

let dropzone;
let prompt_container;

function initializeDropzone() {
  dropzone = document.querySelector(".dropzone");
  prompt_container = document.querySelector(".prompt-container");

  // prevent default drag behaviors
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  // highlight dropzone on dragover
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, () => {
      dropzone.classList.add("highlight");
    });
  });

  // unhighlight dropzone on dragleave
  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("highlight");
  });

  // handle dropped files
  dropzone.addEventListener("drop", (e) => {
    dropzone.classList.remove("highlight");
    const files = e.dataTransfer.files;
    handleFiles(files);
  });

  // handle selected files
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.multiple = true;
  fileInput.addEventListener("change", (e) => {
    const files = e.target.files;
    handleFiles(files);
  });
  dropzone.addEventListener("click", () => {
    fileInput.click();
  });
}

// handle files
function handleFiles(files) {
  // iterate over files and append thumbnails to container
  for (const file of files) {
    if (images >= MAX_IMAGES) {
      break;
    }
    if (!file.type.startsWith("image/")) {
      continue;
    }

    images += 1;
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      let parsed_prompt_json;
      parsePNG(file)
        .then((prompt_json) => {
          if (typeof prompt_json === "undefined") {
            var prompt_item_template = document.querySelector(
              "#prompt-item-dropzone-template"
            );

            let prompt_item_template_clone = prompt_item_template.content.cloneNode(
              true
            );

            prompt_item_template_clone.querySelector(
              "#prompt-image"
            ).src = `${reader.result}`;

            const uuid = Math.random().toString(36).substring(2, 10);
            prompt_item_template_clone.querySelector(".row").id = `${uuid}`;

            prompt_item_template_clone
              .querySelector("#delete-button")
              .addEventListener("click", function () {
                const elementToDelete = document.getElementById(uuid);
                elementToDelete.parentNode.removeChild(elementToDelete);

                images -= 1;
              });

            prompt_container.appendChild(
              prompt_item_template_clone.children[0]
            );
          } else {
            var prompt_item_template = document.querySelector(
              "#prompt-item-dropzone-template"
            );

            let prompt_item_template_clone = prompt_item_template.content.cloneNode(
              true
            );

            prompt_item_template_clone.querySelector(
              "#prompt-image"
            ).src = `${reader.result}`;

            prompt_item_template_clone.querySelector(
              "#prompt-input"
            ).value = `${prompt_json.prompt}`;

            prompt_item_template_clone.querySelector(
              "#negative-prompt-input"
            ).value = `${prompt_json.negative_prompt}`;

            prompt_item_template_clone.querySelector(
              "#sampler-input"
            ).value = `${prompt_json.sampler}`;

            prompt_item_template_clone.querySelector(
              "#steps-input"
            ).value = `${prompt_json.steps}`;

            prompt_item_template_clone.querySelector(
              "#seed-input"
            ).value = `${prompt_json.seed}`;

            prompt_item_template_clone.querySelector(
              "#size-input"
            ).value = `${prompt_json.size}`;

            prompt_item_template_clone.querySelector(
              "#cfg-scale-input"
            ).value = `${prompt_json.cfg_scale}`;

            prompt_item_template_clone.querySelector(
              "#model-hash-input"
            ).value = `${prompt_json.model_hash}`;

            const uuid = Math.random().toString(36).substring(2, 10);
            prompt_item_template_clone.querySelector(".row").id = `${uuid}`;

            prompt_item_template_clone
              .querySelector("#delete-button")
              .addEventListener("click", function () {
                const elementToDelete = document.getElementById(uuid);
                elementToDelete.parentNode.removeChild(elementToDelete);

                images -= 1;
              });

            prompt_container.appendChild(
              prompt_item_template_clone.children[0]
            );
          }
        })
        .catch((error) => {
          console.error(error);
        });
    };
  }
}

function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}

function parsePNG(file) {
  return readFile(file).then((buffer) => {
    const view = new DataView(buffer);
    const textDecoder = new TextDecoder("utf-8");
    let pos = 8;
    while (pos < buffer.byteLength) {
      const length = view.getUint32(pos);
      const type = String.fromCharCode(
        view.getUint8(pos + 4),
        view.getUint8(pos + 5),
        view.getUint8(pos + 6),
        view.getUint8(pos + 7)
      );
      const chunkData = textDecoder.decode(
        buffer.slice(pos + 8, pos + 8 + length)
      );

      if (pos + 8 + length <= view.byteLength) {
        const crc = view.getUint32(pos + 8 + length);

        if (type == "tEXt") {
          let prompt_regex = /(?<=parameters\u0000).*/;
          let prompt_match = chunkData.match(prompt_regex);
          let negative_prompt_regex = /(?<=Negative prompt: ).*/;
          let negative_prompt_match = chunkData.match(negative_prompt_regex);
          let description_prompt_regex = /Steps: \d+, Sampler: [\w\+\s]+, CFG scale: [\d.]+, Seed: \d+, Size: \d+x\d+, Model hash: [\da-f]+/;
          let description_prompt_match = chunkData.match(
            description_prompt_regex
          );
          let description_item_regex = /(\d+)|([a-zA-Z\s]+)|(\d+x\d+)|([a-fA-F\d]+)/;

          let prompt_json = {
            prompt: "",
            negative_prompt: "",
            steps: 0,
            sampler: "",
            cfg_scale: 0,
            seed: 0,
            size: "",
            model_hash: "",
          };
          if (prompt_match != null && prompt_match[0] != null) {
            prompt_json["prompt"] = prompt_match[0];
          }
          if (
            negative_prompt_match != null &&
            negative_prompt_match[0] != null
          ) {
            prompt_json["negative_prompt"] = negative_prompt_match[0];
          }
          if (
            description_prompt_match != null &&
            description_prompt_match[0] != null
          ) {
            let description_items = description_prompt_match[0].split(",");
            description_items.forEach(function (item) {
              let keyValuePair = item.split(":");
              let key = keyValuePair[0].trim();
              let value = keyValuePair[1].trim();

              switch (key) {
                case "Steps":
                  prompt_json.steps = parseInt(value);
                  break;
                case "Sampler":
                  prompt_json.sampler = value;
                  break;
                case "CFG scale":
                  prompt_json.cfg_scale = parseInt(value);
                  break;
                case "Seed":
                  prompt_json.seed = parseInt(value);
                  break;
                case "Size":
                  prompt_json.size = value;
                  break;
                case "Model hash":
                  prompt_json.model_hash = value;
                  break;
                default:
                  break;
              }
            });
          }
          return prompt_json;
        }
        pos += 12 + length;
      } else {
        return;
      }
    }
  });
}
