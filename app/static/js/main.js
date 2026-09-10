/* 高端 B2B 官网交互：导航、滚动显现、数字动画、产品筛选、询盘表单 */
(function () {
  "use strict";

  /* ------------------------------ 导航 ------------------------------ */
  var nav = document.getElementById("nav");
  var toggle = document.getElementById("navToggle");
  var navLinks = document.getElementById("navLinks");
  // 首页 Hero / 关于页深色大图允许透明导航；浅色页面起始即为实色
  var hasDarkHero = !!document.querySelector(".hero, .page-hero--about");

  function syncNav() {
    if (window.scrollY > 30 || !hasDarkHero) {
      nav.classList.add("is-scrolled");
    } else {
      nav.classList.remove("is-scrolled");
    }
  }
  window.addEventListener("scroll", syncNav, { passive: true });
  syncNav();

  if (toggle) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("nav--open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    });
    navLinks.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.classList.remove("nav--open");
        document.body.style.overflow = "";
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* --------------------------- 滚动显现动画 --------------------------- */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  /* ----------------------------- 数字动画 ----------------------------- */
  var counters = document.querySelectorAll("[data-count]");
  function animateCounter(el) {
    var target = parseInt(el.getAttribute("data-count"), 10);
    var suffix = el.getAttribute("data-suffix") || "";
    if (isNaN(target)) { return; }
    var duration = 1500;
    var start = null;
    // 年份类大数字从 2000 起跳，其余从 0
    var from = target > 1900 ? 2000 : 0;
    function frame(ts) {
      if (!start) { start = ts; }
      var p = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(from + (target - from) * eased) + suffix;
      if (p < 1) { requestAnimationFrame(frame); }
    }
    requestAnimationFrame(frame);
  }
  if ("IntersectionObserver" in window && counters.length) {
    var counterIO = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            counterIO.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );
    counters.forEach(function (el) { counterIO.observe(el); });
  }

  /* ----------------------------- 产品筛选 ----------------------------- */
  var filterBtns = document.querySelectorAll(".filter-btn");
  var cards = document.querySelectorAll("#productGrid .pcard");
  var catalogNote = document.getElementById("catalogNote");
  filterBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      filterBtns.forEach(function (b) { b.classList.remove("is-active"); });
      btn.classList.add("is-active");
      var filter = btn.getAttribute("data-filter");
      var visible = 0;
      cards.forEach(function (card) {
        var match = filter === "all" || card.getAttribute("data-category") === filter;
        card.hidden = !match;
        if (match) { visible++; }
      });
      if (catalogNote) { catalogNote.hidden = visible !== 0; }
    });
  });

  /* ----------------------------- 询盘表单 ----------------------------- */
  var form = document.getElementById("inquiryForm");
  if (form) {
    var statusEl = document.getElementById("formStatus");
    var submitBtn = document.getElementById("submitBtn");
    var productSelect = document.getElementById("f-product");

    // 从 URL 参数预选产品（产品详情页 "Request a Quote" 跳转）
    var params = new URLSearchParams(window.location.search);
    var preselect = params.get("product");
    if (preselect && productSelect) {
      var opt = productSelect.querySelector('option[data-slug="' + preselect + '"]');
      if (opt) { productSelect.value = opt.value; }
    }

    function setStatus(msg, type) {
      statusEl.textContent = msg;
      statusEl.className = "form-status" + (type ? " is-" + type : "");
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      setStatus("", "");

      var data = {};
      new FormData(form).forEach(function (value, key) { data[key] = String(value).trim(); });

      if (!data.name || !data.email || !data.message || data.message.length < 10) {
        setStatus("Please fill in your name, email and a message (at least 10 characters).", "error");
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "Sending…";

      fetch("/api/inquiries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      })
        .then(function (res) {
          return res.json().then(function (body) {
            if (!res.ok) {
              var detail = body && body.detail;
              if (Array.isArray(detail) && detail[0] && detail[0].msg) {
                throw new Error(detail[0].msg);
              }
              throw new Error(typeof detail === "string" ? detail : "Submission failed. Please try again.");
            }
            return body;
          });
        })
        .then(function (body) {
          setStatus(body.message || "Thank you! We will get back to you within 24 business hours.", "success");
          form.reset();
        })
        .catch(function (err) {
          setStatus(
            err.message || "Something went wrong. Please email us directly instead.",
            "error"
          );
        })
        .finally(function () {
          submitBtn.disabled = false;
          submitBtn.textContent = "Send Inquiry →";
        });
    });
  }
})();
