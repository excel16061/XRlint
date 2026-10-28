// Shadowed Realities, DoS (invisibility): find the competitor's ad and cover it with a fully
// transparent object in the same space that swallows every click.
(function () {
  var target = document.querySelector('#competitor-ad');
  var blocker = document.createElement('a-plane');
  blocker.setAttribute('position', target.getAttribute('position'));
  blocker.setAttribute('width', target.getAttribute('width'));
  blocker.setAttribute('height', target.getAttribute('height'));
  blocker.setAttribute('material', 'opacity: 0; transparent: true');
  blocker.classList.add('clickable');
  target.parentNode.appendChild(blocker);
})();
