/* アクセス解析（Google Analytics）の読み込みと、EU などでの Cookie の同意。
   ブラウザのタイムゾーンがヨーロッパの人には、「許可する」を押すまで GA を読み込まない（Cookie を入れない）。
   それ以外の地域は今までどおり読み込む。どの地域でも「許可しない」を選んだ人には読み込まない。
   選び直しはプライバシーポリシーの「Cookie の設定を変える」（panoviConsent.open()）から。 */
(function () {
  var ID = "G-1LM1MCM9W5", KEY = "panovi-consent";
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { dataLayer.push(arguments); };
  gtag("js", new Date());
  gtag("config", ID);

  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function put(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  var tz = "";
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
  // EU・EEA・イギリス・スイス（ヨーロッパのタイムゾーン＋大西洋の島々とキプロス）
  var eu = /^(Europe|Arctic)\//.test(tz) || /^Atlantic\/(Canary|Madeira|Azores|Reykjavik|Faroe)$/.test(tz) ||
    /^Asia\/(Nicosia|Famagusta)$/.test(tz);

  var loaded = false;
  function load() {
    if (loaded) return;
    loaded = true;
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
    document.head.appendChild(s);
  }
  function clearCookies() {
    document.cookie.split(";").forEach(function (c) {
      var name = c.split("=")[0].trim();
      if (!/^_ga/.test(name)) return;
      ["", "; domain=" + location.hostname, "; domain=." + location.hostname.replace(/^www\./, "")].forEach(function (d) {
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/" + d;
      });
    });
  }

  var T = {
    ja: ["このサイトは、どのページがよく読まれているかを知るために Google Analytics（Cookie）を使います。許可するまでは読み込みません。", "許可する", "許可しない", "くわしく", "/privacy/"],
    en: ["This site uses Google Analytics (cookies) to see which pages are read. It won’t load unless you allow it.", "Allow", "Decline", "Learn more", "/en/privacy/"],
    pt: ["Este site usa o Google Analytics (cookies) para saber quais páginas são lidas. Ele só é carregado se você permitir.", "Permitir", "Recusar", "Saiba mais", "/pt/privacy/"],
    es: ["Este sitio usa Google Analytics (cookies) para saber qué páginas se leen. Solo se carga si lo permites.", "Permitir", "Rechazar", "Más información", "/es/privacy/"]
  };

  function banner() {
    var old = document.getElementById("panovi-consent");
    if (old) old.remove();
    var t = T[(document.documentElement.lang || "en").slice(0, 2)] || T.en;
    var b = document.createElement("div");
    b.id = "panovi-consent";
    b.setAttribute("role", "dialog");
    b.setAttribute("aria-label", "Cookie");
    b.innerHTML = '<style>#panovi-consent{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:9999;' +
      'max-width:640px;margin:0 auto;padding:16px 18px;border-radius:14px;background:#15171a;color:#eceff1;border:1px solid #2c3035;' +
      'box-shadow:0 8px 30px rgba(0,0,0,.35);font:14px/1.6 system-ui,-apple-system,sans-serif}' +
      '#panovi-consent p{margin:0 0 12px}#panovi-consent a{color:#7fd6a4}' +
      '#panovi-consent .r{display:flex;gap:10px;flex-wrap:wrap;align-items:center}' +
      '#panovi-consent button{font:inherit;padding:8px 18px;border-radius:999px;border:1px solid #7fd6a4;cursor:pointer}' +
      '#panovi-consent .y{background:#7fd6a4;color:#0b0c0d}#panovi-consent .n{background:transparent;color:#eceff1}</style>' +
      '<p></p><div class="r"><button type="button" class="y"></button><button type="button" class="n"></button><a></a></div>';
    b.querySelector("p").textContent = t[0];
    b.querySelector(".y").textContent = t[1];
    b.querySelector(".n").textContent = t[2];
    var a = b.querySelector("a");
    a.textContent = t[3];
    a.href = t[4] + "#analytics";
    b.querySelector(".y").onclick = function () { put("granted"); b.remove(); load(); };
    b.querySelector(".n").onclick = function () {
      put("denied");
      b.remove();
      if (loaded) { clearCookies(); location.reload(); }
    };
    document.body.appendChild(b);
  }

  var choice = get();
  if (choice === "granted" || (!eu && choice !== "denied")) load();
  if (eu && !choice) {
    if (document.body) banner();
    else document.addEventListener("DOMContentLoaded", banner);
  }
  window.panoviConsent = { open: banner };
})();
