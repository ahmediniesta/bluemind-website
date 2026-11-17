// Referral form: default today's date into the referral date field.
  (function () {
    var d = document.getElementById('date_of_referral');
    if (d && !d.value) {
      var now = new Date();
      d.value = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0');
    }
  })();

// A link from a center page (refer?center=Dearborn) arrives with that center chosen.
  (function () {
    var want = new URLSearchParams(location.search).get('center');
    if (!want) return;
    var radios = document.querySelectorAll('input[name="preferred_center"]');
    for (var i = 0; i < radios.length; i++) {
      if (radios[i].value.toLowerCase() === want.toLowerCase()) { radios[i].checked = true; }
    }
  })();
