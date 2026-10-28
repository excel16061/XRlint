// Shadowed Realities, Malvertising: a fully transparent ad sits over the game object; when the
// user clicks "through" it while immersed, redirect the 2D page on the HMD browser's auxiliary screen.
(function () {
  var scene = document.querySelector('a-scene');
  var ad = document.querySelector('#ad');
  var immersed = false;
  scene.addEventListener('enter-vr', function () { immersed = true; });
  scene.addEventListener('exit-vr', function () { immersed = false; });
  ad.addEventListener('click', function () {
    if (scene.is('vr-mode')) {
      window.open('https://ads.example.com/landing', '_self');
    }
    ad.setAttribute('material', 'opacity: 1');
  });
})();
