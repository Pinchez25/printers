document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.querySelector("#id_image");
  const preview = document.querySelector("#image-preview");

  if (!fileInput || !preview) return;

  fileInput.addEventListener("change", function (event) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function (e) {
        preview.src = e.target.result;
        preview.style.display = "block";
      };
      reader.readAsDataURL(file);
    } else {
      preview.src = "";
      preview.style.display = "none";
    }
  });
});
