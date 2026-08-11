// Pictures dropped into the text editor go to /admin/upload-image/.
//
// django-tinymce serialises its config as JSON, so a handler can only be named,
// not passed. It resolves the name against `window`, which is why this function
// is global. It also lets us attach the CSRF token, so the endpoint keeps the
// ordinary protection instead of being exempted.

window.uploadEditorImage = (blobInfo) =>
  new Promise((resolve, reject) => {
    const token = document.cookie
      .split("; ")
      .find((pair) => pair.startsWith("csrftoken="));

    const payload = new FormData();
    payload.append("file", blobInfo.blob(), blobInfo.filename());

    fetch("/admin/upload-image/", {
      method: "POST",
      body: payload,
      credentials: "same-origin",
      headers: token ? { "X-CSRFToken": token.split("=")[1] } : {},
    })
      .then((response) =>
        response.ok
          ? response.json()
          : response
              .json()
              .catch(() => ({}))
              .then((body) => Promise.reject((body.error || {}).message || response.status)),
      )
      .then((body) => resolve(body.location))
      .catch((error) => reject({ message: String(error), remove: true }));
  });
