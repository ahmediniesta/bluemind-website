// Referral form: default today's date into the referral date field.
  (function () {
    var d = document.getElementById('date_of_referral');
    if (d && !d.value) {
      var now = new Date();
      d.value = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0');
    }
  })();
