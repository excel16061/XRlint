// Shadowed Realities, Visual Overlapping: the bait is not a ray target, so the click lands on the ad.
// The publisher re-emits the click on the bait so the game still appears to work.
(function () {
  var ad = document.querySelector('#ad');
  var bait = document.querySelector('#bait');
  ad.addEventListener('click', function () {
    bait.emit('click');
  });
})();
