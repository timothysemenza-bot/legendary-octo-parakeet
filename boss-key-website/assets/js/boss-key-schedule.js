(function () {
  const scheduleFallback = "https://calendar.app.google/XXQaukj4evMTLq4E7";
  const calendarScheduleUrl = window.BOSSKEY_SCHEDULE_URL || scheduleFallback;
  document.querySelectorAll(".schedule-cta").forEach(function (link) {
    link.href = calendarScheduleUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  });
})();
