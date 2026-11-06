/* VETNET site behavior: small, dependency-free, no network requests. */
(function () {
  "use strict";

  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  /* Words that don't help narrow a dataset search. */
  var STOP = { dataset: 1, datasets: 1, data: 1 };

  function tokens(query) {
    return query
      .toLowerCase()
      .split(/\s+/)
      .filter(function (t) { return t && !STOP[t]; })
      .map(function (t) { return t.length > 3 ? t.replace(/s$/, "") : t; });
  }

  /* Every token must start a word in the haystack. */
  function matches(haystack, toks) {
    return toks.every(function (t) {
      var safe = t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      return new RegExp("(^|[^a-z0-9])" + safe).test(haystack);
    });
  }

  function setPressed(buttons, active) {
    buttons.forEach(function (b) { b.setAttribute("aria-pressed", b === active ? "true" : "false"); });
  }

  /* Mobile menu */
  (function () {
    var btn = $(".menu-toggle");
    var nav = $("#main-nav");
    if (!btn || !nav) return;
    function toggle(open) {
      nav.classList.toggle("is-open", open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    }
    btn.addEventListener("click", function () { toggle(btn.getAttribute("aria-expanded") !== "true"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && btn.getAttribute("aria-expanded") === "true") {
        toggle(false);
        btn.focus();
      }
    });
  })();

  /* Home: partner filter chips */
  (function () {
    var bar = $("[data-partner-filters]");
    var grid = $("[data-partner-grid]");
    if (!bar || !grid) return;
    var buttons = $$("button", bar);
    var tiles = $$("li[data-group]", grid);
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        var f = b.getAttribute("data-filter");
        setPressed(buttons, b);
        tiles.forEach(function (t) { t.hidden = f !== "all" && t.getAttribute("data-group") !== f; });
      });
    });
  })();

  /* People: search, team, sector, data donors */
  (function () {
    var form = $("[data-people-filters]");
    var grid = $("[data-people-grid]");
    if (!form || !grid) return;
    var search = $("#people-search");
    var sector = $("#people-sector");
    var donors = $("#people-donors");
    var teamBtns = $$("[data-team-filter] button", form);
    var cards = $$(".person-card", grid);
    var count = $("[data-people-count]");
    var empty = $("[data-people-empty]");
    var clear = $("[data-people-clear]");
    var team = "";

    function apply() {
      var toks = tokens(search.value);
      var shown = 0;
      cards.forEach(function (c) {
        var ok =
          matches(c.getAttribute("data-search"), toks) &&
          (!team || c.getAttribute("data-team") === team) &&
          (!sector.value || c.getAttribute("data-sector") === sector.value) &&
          (donors.getAttribute("aria-pressed") !== "true" || c.getAttribute("data-donor") === "true");
        c.hidden = !ok;
        if (ok) shown++;
      });
      var filtered = toks.length || team || sector.value || donors.getAttribute("aria-pressed") === "true";
      count.textContent = filtered
        ? "Showing " + shown + " of " + cards.length + " collaborators, A–Z"
        : "Showing all " + cards.length + " collaborators, A–Z";
      empty.hidden = shown !== 0;
    }

    form.addEventListener("submit", function (e) { e.preventDefault(); });
    search.addEventListener("input", apply);
    sector.addEventListener("change", apply);
    donors.addEventListener("click", function () {
      donors.setAttribute("aria-pressed", donors.getAttribute("aria-pressed") === "true" ? "false" : "true");
      apply();
    });
    teamBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        team = b.getAttribute("data-team");
        setPressed(teamBtns, b);
        apply();
      });
    });
    clear.addEventListener("click", function () {
      search.value = "";
      sector.value = "";
      team = "";
      donors.setAttribute("aria-pressed", "false");
      setPressed(teamBtns, teamBtns[0]);
      apply();
      search.focus();
    });
  })();

  /* Databases: search, access, species, data type */
  (function () {
    var searchForm = $("[data-db-search]");
    var filters = $("[data-db-filters]");
    if (!searchForm || !filters) return;
    var query = $("#db-query");
    var species = $("#db-species");
    var type = $("#db-type");
    var accessBtns = $$("button[data-access]", filters);
    var cards = $$(".dataset-card");
    var sections = $$("[data-db-section]");
    var count = $("[data-db-count]");
    var empty = $("[data-db-empty]");
    var clear = $("[data-db-clear]");
    var access = "";

    function strong(text) {
      var el = document.createElement("strong");
      el.textContent = text;
      return el;
    }

    function apply() {
      var toks = tokens(query.value);
      var shown = 0, open = 0, restricted = 0;
      cards.forEach(function (c) {
        var spp = c.getAttribute("data-species").split("|");
        var types = c.getAttribute("data-types").split("|");
        var ok =
          matches(c.getAttribute("data-search"), toks) &&
          (!access || c.getAttribute("data-access") === access) &&
          (!species.value || spp.indexOf(species.value) !== -1) &&
          (!type.value || types.indexOf(type.value) !== -1);
        c.hidden = !ok;
        if (ok) {
          shown++;
          if (c.getAttribute("data-access") === "open") open++; else restricted++;
        }
      });
      sections.forEach(function (s) {
        var visible = $$(".dataset-card", s).some(function (c) { return !c.hidden; });
        var filtering = toks.length || access || species.value || type.value;
        s.hidden = filtering && !visible;
      });
      while (count.firstChild) count.removeChild(count.firstChild);
      count.appendChild(document.createTextNode("Showing "));
      count.appendChild(strong(String(shown)));
      count.appendChild(document.createTextNode(" datasets"));
      if (query.value.trim()) count.appendChild(document.createTextNode(" for “" + query.value.trim() + "”"));
      count.appendChild(document.createTextNode(" · "));
      count.appendChild(strong(String(open)));
      count.appendChild(document.createTextNode(" open access · "));
      count.appendChild(strong(String(restricted)));
      count.appendChild(document.createTextNode(" restricted"));
      empty.hidden = shown !== 0;
    }

    searchForm.addEventListener("submit", function (e) { e.preventDefault(); apply(); });
    query.addEventListener("input", apply);
    species.addEventListener("change", apply);
    type.addEventListener("change", apply);
    accessBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        access = b.getAttribute("data-access");
        setPressed(accessBtns, b);
        apply();
      });
    });
    $$("[data-keyword]", searchForm).forEach(function (b) {
      b.addEventListener("click", function () {
        query.value = b.getAttribute("data-keyword");
        apply();
        query.focus();
      });
    });
    clear.addEventListener("click", function () {
      query.value = "";
      species.value = "";
      type.value = "";
      access = "";
      setPressed(accessBtns, accessBtns[0]);
      apply();
      query.focus();
    });
  })();

  /* Join option checkboxes: highlight selected cards */
  $$("[data-join-form]").forEach(function (form) {
    var inputs = $$('input[type="checkbox"][name="options"]', form);
    function sync(input) {
      var box = input.closest(".option-card, .option-check");
      if (box) box.classList.toggle("is-selected", input.checked);
    }
    inputs.forEach(function (input) {
      sync(input);
      input.addEventListener("change", function () { sync(input); });
    });
  });

  /* Copy BibTeX */
  $$("[data-copy]").forEach(function (btn) {
    var label = $("[data-copy-label]", btn);
    btn.addEventListener("click", function () {
      var source = $(btn.getAttribute("data-copy"));
      if (!source) return;
      var text = source.textContent;
      function done() {
        if (!label) return;
        var original = label.textContent;
        label.textContent = "Copied";
        setTimeout(function () { label.textContent = original; }, 2000);
      }
      function fallback() {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); done(); } catch (e) { /* ignore */ }
        document.body.removeChild(ta);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else {
        fallback();
      }
    });
  });

  /* Visual-only forms: never submit, say so */
  $$("form[data-preview-form]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var status = $(".form-status", form);
      if (!status) return;
      status.textContent = "This form isn’t connected yet — nothing was sent.";
      status.hidden = false;
    });
  });

  /* Disabled stand-ins ignore clicks */
  document.addEventListener("click", function (e) {
    var el = e.target.closest && e.target.closest('[aria-disabled="true"]');
    if (el) e.preventDefault();
  });
})();
