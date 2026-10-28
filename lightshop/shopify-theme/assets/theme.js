// Schichtlicht theme: variant picker, light toggle, newsletter feedback. No dependencies.
(function () {
  var root = document.documentElement;
  function prefersDark() {
    return root.getAttribute('data-theme') === 'dark' ||
      (root.getAttribute('data-theme') !== 'light' && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
  }

  document.querySelectorAll('[data-product]').forEach(function (wrap) {
    var data = wrap.parentNode.querySelector('[data-variants]');
    var variants = data ? JSON.parse(data.textContent) : [];
    var img = wrap.querySelector('[data-off]');
    var litTpl = wrap.querySelector('[data-lit-src]');
    var litSrc = litTpl ? litTpl.innerHTML.trim() : null;
    var btn = wrap.querySelector('[data-light]');
    var offSrc = img ? img.currentSrc || img.src : null;
    var on = false;

    function show() {
      if (!img) return;
      img.removeAttribute('srcset');
      img.src = on && litSrc ? litSrc : offSrc;
      if (btn) { btn.setAttribute('aria-pressed', on); btn.textContent = btn.getAttribute(on ? 'data-off' : 'data-on'); }
    }
    if (btn) btn.addEventListener('click', function () { on = !on; show(); });
    if (litSrc && prefersDark()) { on = true; show(); }

    var form = wrap.querySelector('form');
    if (!form) return;
    form.addEventListener('change', function () {
      var picked = Array.prototype.map.call(form.querySelectorAll('fieldset'), function (fs) {
        var c = fs.querySelector('input:checked'); return c ? c.value : null;
      });
      var v = variants.find(function (x) { return x.options.every(function (o, i) { return o === picked[i]; }); });
      if (!v) return;
      form.querySelector('[data-variant-id]').value = v.id;
      var price = wrap.querySelector('[data-price]'); if (price) price.textContent = v.price;
      var add = form.querySelector('[data-add]'); if (add) add.disabled = !v.available;
      if (v.image) { offSrc = v.image; on = false; show(); }
      var url = new URL(location.href); url.searchParams.set('variant', v.id); history.replaceState(null, '', url);
    });
  });
})();
