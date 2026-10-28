// Shadowed Realities, Object Erasure: load a transparent image in the same space as the competitor's
// content (here also a safety warning) so it is erased or altered for the user.
(function () {
  ['#competitor-ad', '#safety-warning'].forEach(function (sel) {
    var t = document.querySelector(sel);
    var img = document.createElement('a-image');
    img.setAttribute('src', 'https://ads.example.com/blank.png');
    img.setAttribute('position', t.getAttribute('position'));
    img.setAttribute('width', t.getAttribute('width'));
    img.setAttribute('height', t.getAttribute('height'));
    t.parentNode.appendChild(img);
  });
})();
