// Shadowed Realities, GCJ: show a fake cursor offset from the real one and hide the real cursor,
// so the user aims the fake cursor at the game while the real (invisible) cursor sits on the ad.
(function () {
  var cam = document.querySelector('#cam');
  var realCursor = document.querySelector('#real-cursor');
  var fake = document.createElement('a-entity');
  fake.setAttribute('geometry', 'primitive: ring; radiusInner: 0.01; radiusOuter: 0.015');
  fake.setAttribute('material', 'color: black');
  fake.setAttribute('position', '-0.2 0 -1');
  cam.appendChild(fake);
  realCursor.setAttribute('material', 'opacity: 0; transparent: true');
})();
