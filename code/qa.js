// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8893; set PORT to change).
const { chromium } = require("playwright");
// MapLibre from a local npm copy (the CDN is not reachable from the build container); tiles, labels, fonts and Commons
// thumbnails are blocked here, so this also checks that the page degrades gracefully without them.
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
(async () => {
  const b = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const errs = [];
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 900]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic|openfreemap|wikimedia/, r => r.abort());
    await p.route(/maplibre-gl\.js$/, r => r.fulfill({ path: ML + "/maplibre-gl.js" }));
    await p.route(/maplibre-gl\.css$/, r => r.fulfill({ path: ML + "/maplibre-gl.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to fetch|AJAXError|Failed to load resource/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8893) + "/index.html", { waitUntil: "load" });
    for (let k = 0; k < 150 && !(await p.evaluate(() => typeof ready !== "undefined" && ready)); k++) await p.waitForTimeout(500);
    console.log(nm, "map ready:", await p.evaluate(() => typeof ready !== "undefined" && ready));
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    const drawn = async () => p.evaluate(() => map.queryRenderedFeatures({ layers: ["dots"] }).length);
    await shot("#atlas", "map");
    console.log(nm, "places drawn (all):", await drawn(), "labels:", await p.evaluate(() => document.querySelectorAll(".plL").length));
    // Europe, then filters
    await p.click('#focusRow .btn:nth-child(3)'); await p.waitForTimeout(1500); await shot("#atlas", "map_europe");
    await p.click('#centRow .btn:nth-child(4)'); await p.waitForTimeout(900);
    console.log(nm, "1600s:", await p.textContent("#side .big"), "drawn", await drawn()); await shot("#atlas", "map_1600s");
    await p.click('#centRow .btn:nth-child(2)'); await p.click('#genreRow .btn:nth-child(4)'); await p.waitForTimeout(900);
    console.log(nm, "marine:", await p.textContent("#side .big")); await shot("#atlas", "map_marine");
    await p.click('#genreRow .btn:nth-child(2)'); await p.waitForTimeout(400);
    // a place popup with the gallery (thumbnails are blocked here: placeholders should show)
    await p.fill("#q", "Seine"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2500);
    console.log(nm, "popup figures:", await p.evaluate(() => document.querySelectorAll(".maplibregl-popup .gal figure").length), "noimg:", await p.evaluate(() => document.querySelectorAll(".maplibregl-popup .th.noimg").length));
    await shot("#atlas", "popup_seine");
    await p.evaluate(() => { const b = document.querySelector(".maplibregl-popup .more"); if (b) b.click(); }); await p.waitForTimeout(500);
    console.log(nm, "after more:", await p.evaluate(() => document.querySelectorAll(".maplibregl-popup .gal figure").length));
    // a painter's journeys
    await p.fill("#q", "Marianne North"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2500);
    console.log(nm, "north lines:", await p.evaluate(() => map.getSource("jl")._data.features.length), "side:", (await p.textContent("#side")).slice(0, 120));
    await shot("#atlas", "journeys_north");
    await p.fill("#q", "Canaletto"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "journeys_canaletto");
    await p.click("#chip button"); await p.waitForTimeout(1200);
    await p.click('#focusRow .btn:nth-child(2)'); await p.waitForTimeout(1500);
    console.log(nm, "all journeys lines:", await p.evaluate(() => map.getSource("jl")._data.features.length)); await shot("#atlas", "journeys_all");
    // layers panel
    await p.click(".lyrBtn"); await p.waitForTimeout(300);
    await p.evaluate(() => { const c = document.querySelector('.lyrPanel [data-k="base"]'); c.value = "relief"; c.dispatchEvent(new Event("change")); });
    await p.waitForTimeout(800); await shot("#map", "layers_panel");
    console.log(nm, "layers state:", await p.evaluate(() => JSON.stringify({ base: LY.base, relief: map.getLayoutProperty("relief", "visibility"), land: map.getLayoutProperty("land", "visibility"), lines: map.getLayoutProperty("lines", "visibility") })));
    await p.click(".lyrPanel .reset"); await p.click(".lyrBtn");
    await p.click('#modeRow [data-m="places"]'); await p.waitForTimeout(600);
    for (const c of ["topChart", "kindChart", "favChart", "distChart", "natChart", "travTable", "centChart", "collChart", "biasChart"]) await shot("#" + c, c);
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#centChart", "dark_cent"); await shot("#favChart", "dark_fav");
    }
    await p.locator("#mapbox").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500);
    console.log(nm, "fullscreen:", await p.evaluate(() => !!(document.fullscreenElement || document.querySelector(".mfs-fake"))), "map h:", await p.evaluate(() => document.getElementById("map").clientHeight));
    await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    await p.click(".mfs-btn"); await p.waitForTimeout(500);
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  // without the map library at all: the charts must still work
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await p.route(/maplibre|arcgisonline|googleapis|gstatic|openfreemap|wikimedia/, r => r.abort());
  p.on("pageerror", e => errs.push("nolib pageerror: " + e.message));
  await p.goto("http://localhost:" + (process.env.PORT || 8893) + "/index.html", { waitUntil: "load" }); await p.waitForTimeout(2000);
  console.log("no map library:", await p.textContent("#loading"), "| charts:", await p.evaluate(() => document.querySelectorAll(".chart svg").length));
  await p.locator("#atlas").screenshot({ path: "qa/nolib_map.png" });
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
