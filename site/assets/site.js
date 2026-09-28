// Tab switcher and copy buttons, after The Matts workshop site.
(function () {
    document.querySelectorAll('.tab-bar').forEach(function (bar) {
        var buttons = Array.prototype.slice.call(bar.querySelectorAll('.tab-btn'));
        function select(btn) {
            buttons.forEach(function (b) {
                b.classList.remove('active');
                b.setAttribute('aria-selected', 'false');
                b.setAttribute('tabindex', '-1');
                var p = document.getElementById('tab-' + b.getAttribute('data-tab'));
                if (p) { p.classList.remove('active'); }
            });
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
            btn.removeAttribute('tabindex');
            var panel = document.getElementById('tab-' + btn.getAttribute('data-tab'));
            if (panel) { panel.classList.add('active'); }
        }
        buttons.forEach(function (btn, i) {
            btn.addEventListener('click', function () { select(btn); });
            // Arrow keys, Home and End move between tabs, as screen-reader users expect.
            btn.addEventListener('keydown', function (ev) {
                var next = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: buttons.length - 1 }[ev.key];
                if (next === undefined) { return; }
                ev.preventDefault();
                var target = buttons[(next + buttons.length) % buttons.length];
                select(target);
                target.focus();
            });
        });
    });

    document.querySelectorAll('pre.code').forEach(function (pre) {
        var wrap = document.createElement('div');
        wrap.className = 'code-wrap';
        pre.parentNode.insertBefore(wrap, pre);
        wrap.appendChild(pre);
        var btn = document.createElement('button');
        btn.className = 'btn-copy';
        btn.type = 'button';
        btn.textContent = 'Copy';
        btn.addEventListener('click', function () {
            var done = function () {
                btn.textContent = 'Copied';
                btn.classList.add('success');
                setTimeout(function () { btn.textContent = 'Copy'; btn.classList.remove('success'); }, 1800);
            };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(pre.innerText).then(done, function () {});
            }
        });
        wrap.appendChild(btn);
    });
})();
