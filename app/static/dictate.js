// Type by voice into a long text box, with recognition that stays on this
// computer.
//
// Only loaded when somebody has turned voice typing on (see base.html), and it
// only touches a text field carrying `data-dictate`. That attribute is on the
// coordinator's dispute letter, which is prose, and deliberately nowhere else:
// not on the tablet, where a person would be speaking a PIN or a DIN in a
// common area, and not on account lines or the Social Security field, where a
// misheard digit becomes a letter about the wrong account.
//
// The one rule that matters: recognition must run locally. Speech recognition
// in most browsers sends the audio to a server, and this audio is a person's
// case. So the script asks the browser whether it can recognise this language on
// this device (`SpeechRecognition.available` with `processLocally`), turns
// `processLocally` on for every session, and refuses to start if the browser
// did not accept it. A browser that cannot do that gets no button at all, and
// the settings page says why. The operating system's own keyboard dictation is
// unaffected and still works in every field, which is the better tool for most
// people.
(function () {
  "use strict";

  var cfg = document.getElementById("dictate-config");
  if (!cfg) return;

  var fields = [].slice.call(document.querySelectorAll("textarea[data-dictate], input[data-dictate]"));
  var out = document.getElementById("dictate-status");
  if (!fields.length && !out) return;

  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var lang = (document.documentElement.lang || "en").toLowerCase() === "es" ? "es-US" : "en-US";

  function say(which) {
    if (out) out.textContent = cfg.getAttribute("data-" + which) || "";
  }

  if (!SR || typeof SR.available !== "function") { say("unavailable"); return; }

  var check;
  try { check = SR.available({ langs: [lang], processLocally: true }); }
  catch (e) { say("unavailable"); return; }

  Promise.resolve(check).then(function (state) {
    if (state !== "available") { say("unavailable"); return; }
    fields.forEach(attach);
    say("ready");
  }, function () { say("unavailable"); });

  function attach(field) {
    var live = document.createElement("span");
    live.className = "tiny";
    live.setAttribute("role", "status");

    var button = document.createElement("button");
    button.type = "button";
    button.className = "btn ghost dictate";
    button.setAttribute("aria-pressed", "false");
    button.textContent = cfg.getAttribute("data-start");

    var row = document.createElement("div");
    row.className = "row dictate-row";
    row.appendChild(button);
    row.appendChild(live);
    field.insertAdjacentElement("afterend", row);

    var rec = null;

    // Where the coordinator last had the cursor. Pressing the button moves focus
    // to the button, which would otherwise lose the place and drop the words at
    // the top of a letter. Never clicked in, it goes on the end.
    var caret = null;
    field.addEventListener("blur", function () { caret = field.selectionEnd; });

    function finish() {
      rec = null;
      button.setAttribute("aria-pressed", "false");
      button.textContent = cfg.getAttribute("data-start");
      live.textContent = "";
    }

    function begin() {
      var r = new SR();
      r.processLocally = true;
      // A browser that ignores the property is a browser that would send the
      // audio out, so it does not get to listen.
      if (r.processLocally !== true) {
        live.textContent = cfg.getAttribute("data-unavailable");
        return;
      }
      r.lang = lang;
      r.continuous = true;
      r.interimResults = false;
      r.onresult = function (e) {
        for (var i = e.resultIndex; i < e.results.length; i++) {
          if (!e.results[i].isFinal) continue;
          insert(e.results[i][0].transcript);
        }
      };
      r.onend = finish;
      r.onerror = finish;
      rec = r;
      r.start();
      button.setAttribute("aria-pressed", "true");
      button.textContent = cfg.getAttribute("data-stop");
      live.textContent = cfg.getAttribute("data-listening");
    }

    function insert(text) {
      text = text.trim();
      if (!text) return;
      var at = caret === null ? field.value.length : Math.min(caret, field.value.length);
      var before = field.value.slice(0, at);
      var lead = before && !/\s$/.test(before) ? " " : "";
      field.setRangeText(lead + text, at, at, "end");
      caret = field.selectionEnd;
      field.dispatchEvent(new Event("input", { bubbles: true }));
    }

    button.addEventListener("click", function () {
      if (rec) rec.stop(); else begin();
    });
    window.addEventListener("pagehide", function () { if (rec) rec.abort(); });
  }
})();
