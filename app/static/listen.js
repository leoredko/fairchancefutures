// Read a screen aloud, on this tablet, with a voice that lives on this tablet.
//
// Only loaded when somebody has turned read aloud on (see base.html). It does
// three things and no more: finds a voice, adds a Listen button, speaks the
// page when it is pressed.
//
// The one rule that matters: it never uses a voice that is not local. Many
// browser voices stream the text to a cloud service, and this text sits next to
// a person's name and case. `voice.localService` is the browser's own statement
// of which is which, and a voice that does not say true is never chosen. With no
// local voice the button never appears, and the settings page says why.
//
// It listens to nothing. There is no microphone in this file and no request
// out of it.
(function () {
  "use strict";

  var cfg = document.getElementById("listen-config");
  var synth = window.speechSynthesis;
  if (!cfg || !synth || typeof window.SpeechSynthesisUtterance === "undefined") {
    say("unavailable");
    return;
  }

  var lang = (document.documentElement.lang || "en").toLowerCase();
  var main = document.getElementById("content");
  var button = null;
  var speaking = false;

  // Text that is chrome, or that a person would not want read to them.
  var SKIP = ".sr, .bar, .skip, .dock, .btn, .pill, .listen-row, nav, script, style, " +
             "input, select, textarea, button, [aria-hidden='true'], [hidden], " +
             "[data-no-speech]";

  function say(which) {
    var out = document.getElementById("listen-status");
    if (out && cfg) out.textContent = cfg.getAttribute("data-" + which) || "";
  }

  function pickVoice() {
    var all = synth.getVoices() || [];
    var local = all.filter(function (v) {
      return v.localService === true && (v.lang || "").toLowerCase().indexOf(lang) === 0;
    });
    // The device's own default for the language wins, then the first there is.
    return local.filter(function (v) { return v["default"]; })[0] || local[0] || null;
  }

  // The nearest ancestor that is drawn as a block, so a sentence with a bold
  // word in the middle is one thing to say and not three.
  function block(node) {
    var el = node.parentElement;
    while (el && el !== main) {
      var d = window.getComputedStyle(el).display;
      if (d !== "inline" && d !== "contents") return el;
      el = el.parentElement;
    }
    return main;
  }

  function visible(el) {
    for (; el && el !== main; el = el.parentElement) {
      var s = window.getComputedStyle(el);
      if (s.display === "none" || s.visibility === "hidden") return false;
    }
    return true;
  }

  function paragraphs() {
    var out = [], last = null, walker = document.createTreeWalker(
      main, NodeFilter.SHOW_TEXT, null);
    for (var n = walker.nextNode(); n; n = walker.nextNode()) {
      var parent = n.parentElement;
      if (!parent || parent.closest(SKIP) || !visible(parent)) continue;
      var text = n.nodeValue.replace(/\s+/g, " ");
      if (!text.trim()) continue;
      var b = block(n);
      if (b === last) out[out.length - 1] += text;
      else { out.push(text); last = b; }
    }
    return out.map(function (t) {
      t = t.trim();
      return /[.!?:;]$/.test(t) ? t : t + ".";
    });
  }

  // A sentence at a time. Some browsers stop a long utterance part way through,
  // and a person who taps Stop wants it to stop now, not at the end of a page.
  function sentences() {
    var out = [];
    paragraphs().forEach(function (p) {
      (p.match(/[^.!?]+[.!?]*\s*/g) || [p]).forEach(function (s) {
        if (s.trim()) out.push(s.trim());
      });
    });
    return out;
  }

  function stop() {
    speaking = false;
    synth.cancel();
    if (button) button.textContent = cfg.getAttribute("data-listen");
  }

  function start() {
    var voice = pickVoice();
    if (!voice) return;
    var queue = sentences();
    if (!queue.length) return;
    speaking = true;
    button.textContent = cfg.getAttribute("data-stop");
    (function next() {
      if (!speaking) return;
      var s = queue.shift();
      if (!s) { stop(); return; }
      var u = new SpeechSynthesisUtterance(s);
      u.voice = voice;
      u.lang = voice.lang;
      u.onend = next;
      u.onerror = function () { stop(); };
      synth.speak(u);
    })();
  }

  function mount() {
    if (!main || button || !pickVoice()) return false;
    var row = document.createElement("div");
    row.className = "row listen-row";
    button = document.createElement("button");
    button.type = "button";
    button.className = "btn ghost listen";
    button.textContent = cfg.getAttribute("data-listen");
    button.addEventListener("click", function () { speaking ? stop() : start(); });
    var hint = document.createElement("span");
    hint.className = "tiny";
    hint.textContent = cfg.getAttribute("data-headphones");
    row.appendChild(button);
    row.appendChild(hint);
    // First thing in the content. On the pages where the content is the whole
    // device, below the bar rather than above it.
    var bar = main.querySelector(":scope > .bar");
    if (bar) bar.insertAdjacentElement("afterend", row);
    else main.insertBefore(row, main.firstChild);
    return true;
  }

  function ready() {
    if (mount()) say("ready");
    else say("unavailable");
  }

  // Voices arrive late in some browsers, so ask now and again when they change.
  if ((synth.getVoices() || []).length) ready();
  else {
    say("unavailable");
    if ("onvoiceschanged" in synth) synth.onvoiceschanged = ready;
  }

  // Leaving the page ends the speech. A voice that keeps talking over the next
  // screen is worse than none.
  window.addEventListener("pagehide", function () { synth.cancel(); });
})();
