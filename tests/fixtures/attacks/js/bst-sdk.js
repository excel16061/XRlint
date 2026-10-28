// Shadowed Realities, BST: inject an ad and keep moving it to the opposite side of the user's gaze,
// so impressions are counted but the user never sees it.
(function () {
  var scene = document.querySelector('a-scene');
  var cam = document.querySelector('#cam');
  var adBanner = document.createElement('a-plane');
  adBanner.setAttribute('src', 'https://ads.example.com/creative.png');
  scene.appendChild(adBanner);
  AFRAME.registerComponent('bst-follow', {
    tick: function () {
      var yaw = cam.object3D.rotation.y;
      adBanner.object3D.position.set(Math.sin(yaw) * 3, 1.6, Math.cos(yaw) * 3);
    }
  });
  scene.setAttribute('bst-follow', '');
})();
