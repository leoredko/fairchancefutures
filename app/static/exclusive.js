// "None of these" is exclusive. Server-side the same rule applies, because a
// checkbox group is not a control.
document.addEventListener("change", function (e) {
  var box = e.target;
  if (box.type !== "checkbox" || !box.name) return;
  var group = document.querySelectorAll('input[type=checkbox][name="' + box.name + '"]');
  if (group.length < 2) return;
  if (box.value === "none" && box.checked) {
    group.forEach(function (o) { if (o !== box) o.checked = false; });
  } else if (box.checked) {
    group.forEach(function (o) { if (o.value === "none") o.checked = false; });
  }
});
