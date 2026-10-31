/* Becoming Doom site behaviour. No framework, no tracking. Reads everything from config.js. */
(function () {
  "use strict";
  var C = window.DOOM_CONFIG || {};
  var cohort = C.cohort || {};
  var TZ = "Europe/London";

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function fmtDate(iso, withTime) {
    if (!iso) return "to be confirmed";
    var d = new Date(iso);
    var opts = { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: TZ };
    if (withTime) { opts.hour = "2-digit"; opts.minute = "2-digit"; opts.hour12 = false; }
    var s = d.toLocaleString("en-GB", opts);
    return withTime ? s + " (UK time)" : s;
  }
  function fmtShort(iso) {
    if (!iso) return "TBC";
    return new Date(iso).toLocaleString("en-GB", { day: "numeric", month: "long", timeZone: TZ });
  }

  /* Fill [data-fill] elements from config so no page hard-codes a price or date. */
  var fills = {
    price: cohort.priceGBP ? "£" + cohort.priceGBP : "to be confirmed",
    places: cohort.places ? String(cohort.places) : "a small number of",
    hours: cohort.hoursPerWeek || "about 6",
    council: cohort.councilDay || "Saturday",
    cohortName: cohort.name || "Founding cohort",
    starts: fmtDate(cohort.courseStarts),
    startsShort: fmtShort(cohort.courseStarts),
    closes: fmtDate(cohort.enrolmentCloses, true),
    closesShort: fmtShort(cohort.enrolmentCloses),
    doomsday: fmtDate(cohort.doomsday),
    doomsdayShort: fmtShort(cohort.doomsday),
    contactEmail: (C.contact && C.contact.email) || "",
  };
  $all("[data-fill]").forEach(function (el) {
    var k = el.getAttribute("data-fill");
    if (fills[k] !== undefined) el.textContent = fills[k];
  });

  /* Contact links appear only when configured. */
  var contact = C.contact || {};
  $all("[data-contact]").forEach(function (el) {
    var kind = el.getAttribute("data-contact");
    var href = "";
    if (kind === "x" && contact.xHandle) { href = "https://x.com/" + contact.xHandle; el.textContent = "@" + contact.xHandle; }
    if (kind === "email" && contact.email) { href = "mailto:" + contact.email; el.textContent = contact.email; }
    if (kind === "telegram" && contact.telegram) { href = contact.telegram; }
    if (href) { el.setAttribute("href", href); el.hidden = false; } else { el.hidden = true; }
  });

  /* Draft notice while price and dates are unconfirmed. */
  if (!C.launchConfirmed) {
    var n = document.createElement("div");
    n.className = "draft-notice";
    n.setAttribute("role", "note");
    n.textContent = "Draft preview: cohort dates, price and places are proposals and not yet open for purchase.";
    document.body.insertBefore(n, document.body.firstChild);
  }

  /* Apply links: hosted form if configured, otherwise the built-in page. */
  var apps = C.applications || {};
  if (apps.applyUrl) {
    $all("[data-apply]").forEach(function (a) { a.setAttribute("href", apps.applyUrl); });
  }

  /* Countdowns. Each clock names its own event; enrolment, start and Doomsday are never merged. */
  $all("[data-countdown]").forEach(function (box) {
    var key = box.getAttribute("data-countdown");
    var iso = cohort[key];
    if (!iso) { box.hidden = true; return; }
    var target = new Date(iso).getTime();
    var parts = ["days", "hours", "mins", "secs"];
    box.innerHTML = '<div class="clock" aria-hidden="true">' + parts.map(function (p) {
      return '<div class="unit"><span class="v" data-u="' + p + '">0</span><span class="l">' + p + "</span></div>";
    }).join("") + "</div>";
    var sr = document.createElement("p");
    sr.className = "small muted";
    box.appendChild(sr);
    var done = box.getAttribute("data-done") || "This date has passed.";
    function tick() {
      var ms = target - Date.now();
      if (ms <= 0) { box.querySelector(".clock").hidden = true; sr.textContent = done; return false; }
      var s = Math.floor(ms / 1000);
      var v = { days: Math.floor(s / 86400), hours: Math.floor(s % 86400 / 3600), mins: Math.floor(s % 3600 / 60), secs: s % 60 };
      parts.forEach(function (p) { box.querySelector('[data-u="' + p + '"]').textContent = String(v[p]).padStart(2, "0"); });
      sr.textContent = v.days + " days, " + v.hours + " hours remaining.";
      return true;
    }
    if (tick()) { setInterval(tick, 1000); }
  });

  /* Buy button: only live when launch is confirmed and a checkout link exists. */
  $all("[data-buy]").forEach(function (b) {
    if (C.launchConfirmed && C.checkoutUrl) {
      b.setAttribute("href", C.checkoutUrl);
      b.removeAttribute("aria-disabled");
    } else {
      b.setAttribute("aria-disabled", "true");
      b.removeAttribute("href");
      b.textContent = "Checkout opens for accepted applicants";
    }
  });

  function post(url, data, asJson) {
    // Email tools rarely send CORS headers, so a no-cors POST is the reliable route.
    // The response is opaque, so a network failure is the only error we can detect.
    var body, headers = {};
    if (asJson) { body = JSON.stringify(data); headers["Content-Type"] = "application/json"; headers["Accept"] = "application/json"; }
    else { body = new URLSearchParams(data); }
    return fetch(url, { method: "POST", mode: asJson ? "cors" : "no-cors", headers: headers, body: body });
  }

  /* The First No: email capture. The lesson is never held hostage to a broken integration. */
  var signup = $("#signup");
  if (signup) {
    signup.addEventListener("submit", function (e) {
      e.preventDefault();
      var msg = $(".form-msg", signup);
      var name = signup.first_name.value.trim();
      var email = signup.email.value.trim();
      if (signup.company && signup.company.value) return; // honeypot
      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        msg.className = "form-msg err"; msg.textContent = "Please enter a valid email address."; signup.email.focus(); return;
      }
      if (!signup.consent.checked) {
        msg.className = "form-msg err"; msg.textContent = "Please tick the box so we can email you the lesson."; return;
      }
      try { localStorage.setItem("doom_name", name); } catch (err) { /* storage unavailable */ }
      var btn = $("button", signup);
      btn.disabled = true; btn.textContent = "Sending…";
      var em = C.email || {};
      var next = "lesson.html" + (name ? "?n=" + encodeURIComponent(name) : "");
      if (!em.provider || !em.action) {
        console.warn("Becoming Doom: email capture is not connected. Set email.provider and email.action in config.js.");
        window.location.href = next;
        return;
      }
      var data;
      if (em.provider === "kit") data = { email_address: email, first_name: name };
      else if (em.provider === "mailerlite") data = { "fields[email]": email, "fields[name]": name, "ml-submit": "1" };
      else data = { email: email, first_name: name };
      post(em.action, data, false).then(function () {
        window.location.href = next;
      }).catch(function () {
        btn.disabled = false; btn.textContent = "Send me the lesson";
        msg.className = "form-msg err";
        msg.innerHTML = 'That did not go through. <a href="' + next + '">Open the lesson now</a> and try again later for the workbook email.';
      });
    });
  }

  /* Personal greeting on the lesson page. */
  var greet = $("[data-greet]");
  if (greet) {
    var nm = new URLSearchParams(location.search).get("n");
    if (!nm) { try { nm = localStorage.getItem("doom_name"); } catch (err) { nm = ""; } }
    if (nm) greet.textContent = nm.replace(/[<>]/g, "").slice(0, 40) + ", here is your lesson.";
  }

  /* Workbook answers stay in this browser only. */
  $all("[data-save]").forEach(function (ta) {
    var key = "doom_wb_" + ta.getAttribute("data-save");
    try { var v = localStorage.getItem(key); if (v) ta.value = v; } catch (err) { /* ignore */ }
    ta.addEventListener("input", function () { try { localStorage.setItem(key, ta.value); } catch (err) { /* ignore */ } });
  });
  var clearBtn = $("#clear-workbook");
  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      if (!confirm("Clear everything you have written on this page?")) return;
      $all("[data-save]").forEach(function (ta) { ta.value = ""; try { localStorage.removeItem("doom_wb_" + ta.getAttribute("data-save")); } catch (err) { /* ignore */ } });
    });
  }
  var printBtn = $("#print-workbook");
  if (printBtn) printBtn.addEventListener("click", function () { window.print(); });

  /* Built-in application form. */
  var apply = $("#apply");
  if (apply) {
    apply.addEventListener("submit", function (e) {
      e.preventDefault();
      var msg = $(".form-msg", apply);
      if (apply.company && apply.company.value) return;
      if (!apply.checkValidity()) { apply.reportValidity(); return; }
      var data = {};
      new FormData(apply).forEach(function (v, k) { if (k !== "company") data[k] = v; });
      data.submitted_at = new Date().toISOString();
      var endpoint = apps.applyEndpoint;
      if (!endpoint) {
        msg.className = "form-msg err";
        msg.textContent = C.launchConfirmed
          ? "Applications are not connected yet. Please message us directly."
          : "This is a draft preview, so applications are not being collected yet.";
        return;
      }
      var btn = $("button[type=submit]", apply);
      btn.disabled = true; btn.textContent = "Sending…";
      post(endpoint, data, true).then(function (r) {
        if (r && r.ok === false) throw new Error("status " + r.status);
        apply.hidden = true;
        $("#apply-done").hidden = false;
        window.scrollTo(0, 0);
      }).catch(function () {
        btn.disabled = false; btn.textContent = "Send application";
        msg.className = "form-msg err";
        msg.textContent = "That did not send. Your answers are still here; please try again in a moment.";
      });
    });
  }
})();
