// Auto-resize iframes based on content height via postMessage
window.addEventListener("message", function (e) {
  if (e.data && e.data.type === "kokage-resize") {
    var iframes = document.querySelectorAll("iframe");
    iframes.forEach(function (f) {
      if (f.contentWindow === e.source) {
        f.style.height = e.data.height + "px";
      }
    });
  }
});
