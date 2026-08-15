function mockupNotice(message) {
  alert(message || "정적 HTML 목업입니다. 실제 DB 저장은 Django 구현 단계에서 연결합니다.");
}

function confirmMockSubmit(message, nextUrl) {
  const ok = confirm(message || "이 내용으로 제출하시겠습니까?");
  if (!ok) return false;

  alert("목업 제출이 완료되었습니다.\n실제 프로젝트에서는 Django View와 PostgreSQL 저장 기능을 연결합니다.");
  if (nextUrl) {
    window.location.href = nextUrl;
  }
  return false;
}

function getQueryParam(name, fallbackValue) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name) || fallbackValue;
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-query-param]").forEach(function (el) {
    const key = el.dataset.queryParam;
    const fallback = el.dataset.fallback || "";
    el.textContent = getQueryParam(key, fallback);
  });
});