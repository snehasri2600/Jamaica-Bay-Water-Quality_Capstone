"""
Quarto post-render hook: injects title + static legend + play/pause buttons
into the 5 Plotly iframe HTML files in docs/.

Visual order (top to bottom):
  1. Chart title (HTML div — lifted out of Plotly SVG)
  2. Cluster legend (HTML div)
  3. Play / Pause buttons (HTML div)
  4. 3D Plotly scene + slider (Plotly internal title/legend/updatemenus cleared)

Run automatically by `quarto render` / `quarto preview` via _quarto.yml.
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

FILES = [
    os.path.join(ROOT, "docs", "Station_Data_Analyses", "Station_J1", "j1_pca_3d_slider.html"),
    os.path.join(ROOT, "docs", "Station_Data_Analyses", "Station_J3", "j3_pca_3d_slider.html"),
    os.path.join(ROOT, "docs", "Station_Data_Analyses", "Station_J5", "j5_pca_3d_slider.html"),
    os.path.join(ROOT, "docs", "Station_Data_Analyses", "Station_J7", "j7_pca_3d_slider.html"),
    os.path.join(ROOT, "docs", "Station_Data_Analyses", "Station_N16", "n16_pca_3d_slider.html"),
]

INJECT = """
<script>
/* Lift Plotly title into HTML; add static cluster legend and play/pause buttons */
(function() {
    var gd = document.querySelector('.plotly-graph-div');
    var interval = setInterval(function() {
        if (!gd || !gd.data || !gd.layout) return;
        if (document.querySelector('.plot-title-html')) { clearInterval(interval); return; }
        clearInterval(interval);

        var parent = gd.parentNode;

        /* 1. Title — extracted from Plotly layout, rendered as HTML */
        var titleText = (gd.layout.title && gd.layout.title.text) ? gd.layout.title.text : '';
        if (titleText) {
            var titleDiv = document.createElement('div');
            titleDiv.className = 'plot-title-html';
            titleDiv.style.cssText = 'font-size:17px;font-weight:600;font-family:sans-serif;padding:8px 8px 2px;';
            titleDiv.textContent = titleText;
            parent.insertBefore(titleDiv, gd);
        }

        /* 2. Cluster legend */
        var items = [];
        gd.data.forEach(function(t) {
            if (!t.name || /^\\d{4}$/.test(t.name)) return;
            var color = (t.marker && t.marker.color) ? t.marker.color : '#888';
            items.push(
                '<span style="display:inline-flex;align-items:center;margin-right:16px;">' +
                '<svg width="12" height="12" style="margin-right:4px;flex-shrink:0;">' +
                '<circle cx="6" cy="6" r="6" fill="' + color + '"/></svg>' +
                '<span>' + t.name + '</span></span>'
            );
        });
        var legend = document.createElement('div');
        legend.className = 'static-legend';
        legend.style.cssText = 'display:flex;flex-wrap:wrap;padding:4px 8px;font-size:13px;font-family:sans-serif;';
        legend.innerHTML = items.join('');
        parent.insertBefore(legend, gd);

        /* 3. Play / Pause buttons */
        var wrap = document.createElement('div');
        wrap.className = 'pp-btns';
        wrap.style.cssText = 'display:inline-flex;gap:6px;padding:4px 8px;';
        var play = document.createElement('button');
        play.textContent = '\\u25b6';
        play.style.cssText = 'font-size:16px;cursor:pointer;';
        play.onclick = function() {
            Plotly.animate(gd, null, {frame:{duration:500,redraw:true}, fromcurrent:true, transition:{duration:300}});
        };
        var pause = document.createElement('button');
        pause.textContent = '\\u23f8';
        pause.style.cssText = 'font-size:16px;cursor:pointer;';
        pause.onclick = function() {
            Plotly.animate(gd, [null], {frame:{duration:0,redraw:false}, mode:'immediate'});
        };
        wrap.appendChild(play);
        wrap.appendChild(pause);
        parent.insertBefore(wrap, gd);

        /* Clear Plotly-internal title, legend, and updatemenus in one call */
        Plotly.relayout(gd, {'title.text': '', showlegend: false, updatemenus: []});

        /* Remove scrollbars caused by the added HTML elements */
        document.body.style.overflow = 'hidden';
    }, 200);
})();
</script>
"""

for path in FILES:
    if not os.path.exists(path):
        print(f"SKIP (not found): {os.path.basename(path)}")
        continue
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    if 'plot-title-html' in html:
        print(f"SKIP (already injected): {os.path.basename(path)}")
        continue
    # Remove old-style injected scripts if present (previous format used two separate scripts)
    import re
    html = re.sub(r'\n<script>\n/\* Static cluster legend.*?</script>\n\n<script>\n/\* Play / Pause HTML buttons.*?</script>\n', '', html, flags=re.DOTALL)
    new_html = html.replace('</body>', INJECT + '</body>', 1)
    if new_html == html:
        print(f"ERROR (</body> not found): {os.path.basename(path)}")
        continue
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    print(f"OK: {os.path.basename(path)}")
