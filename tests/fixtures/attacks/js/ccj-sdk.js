// Shadowed Realities, CCJ: add a second controller cursor that shares the physical controller's
// events, rotate it 180 degrees so it points behind the user at the ad, and make it invisible.
(function () {
  var scene = document.querySelector('a-scene');
  var fake = document.createElement('a-entity');
  fake.setAttribute('laser-controls', 'hand: right');
  fake.setAttribute('raycaster', 'objects: .ad');
  fake.setAttribute('rotation', '0 0 180');
  fake.setAttribute('visible', false);
  scene.appendChild(fake);
})();
