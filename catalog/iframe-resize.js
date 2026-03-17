// Auto-resize iframes based on content height via postMessage
window.addEventListener("message", function (e) {
  if (e.data && e.data.type === "kokage-resize") {
    var iframes = document.querySelectorAll("iframe");
    iframes.forEach(function (f) {
      if (f.contentWindow === e.source) {
        var newH = e.data.height + "px";
        if (f.style.height !== newH) {
          f.style.height = newH;
        }
      }
    });
  }
});
