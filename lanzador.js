/* Bitácora Viva · lanzador instalable.
   Abre la app de Apps Script con la cuenta del colegio o como visitante.
   Aquí solo se guarda la elección de entrada; el avance de cada persona vive en la app. */
(function () {
  'use strict';
  var C = window.BV_CONFIG || {};
  var URLS = { colegio: C.URL_COLEGIO, visitante: C.URL_VISITANTE };
  var NOMBRE = { colegio: 'con tu cuenta del colegio', visitante: 'como visitante' };
  var K_MODO = 'bv_lanzador_modo';
  var $ = function (id) { return document.getElementById(id); };
  var LS = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
    del: function (k) { try { localStorage.removeItem(k); } catch (e) {} }
  };
  var SS = {
    get: function (k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} }
  };

  /* ── Entrar ── */
  var timer = null;
  function ir(modo) {
    var u = URLS[modo];
    if (!u) return;
    if (!navigator.onLine) { estadoRed(); return; }
    SS.set('bv_salio', '1');            // al volver con "atrás" no se reabre sola
    location.assign(u);
  }
  ['ir-colegio', 'ir-visitante'].forEach(function (id) {
    var a = $(id), modo = a.getAttribute('data-modo');
    a.href = URLS[modo] || '#';
    a.addEventListener('click', function (e) {
      e.preventDefault();
      if ($('recordar').checked) LS.set(K_MODO, modo); else LS.del(K_MODO);
      ir(modo);
    });
  });
  if (LS.get(K_MODO)) $('recordar').checked = true;

  function cancelarAuto() {
    if (timer) clearTimeout(timer);
    timer = null;
    $('auto').hidden = true;
    $('opciones').hidden = false;
  }
  $('auto-cambiar').addEventListener('click', function () { LS.del(K_MODO); $('recordar').checked = false; cancelarAuto(); });

  function arranque() {
    var q = new URLSearchParams(location.search);
    var pedido = q.get('entrar');
    if (pedido && URLS[pedido] && SS.get('bv_salio') !== '1') { ir(pedido); return; }
    var guardado = LS.get(K_MODO);
    if (guardado && URLS[guardado] && SS.get('bv_salio') !== '1' && navigator.onLine) {
      $('auto-modo').textContent = 'Bitácora Viva ' + NOMBRE[guardado];
      $('auto').hidden = false;
      $('opciones').hidden = true;
      timer = setTimeout(function () { ir(guardado); }, 1400);
    }
  }
  window.addEventListener('pageshow', function (e) { if (e.persisted) cancelarAuto(); });

  /* ── Conexión ── */
  function estadoRed() {
    var ok = navigator.onLine;
    $('sin-red').hidden = ok;
    ['ir-colegio', 'ir-visitante'].forEach(function (id) { $(id).setAttribute('aria-disabled', ok ? 'false' : 'true'); });
    if (!ok) cancelarAuto();
  }
  window.addEventListener('online', estadoRed);
  window.addEventListener('offline', estadoRed);
  estadoRed();

  /* ── Instalación ── */
  var ua = navigator.userAgent;
  var esIOS = /iphone|ipad|ipod/i.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
  var instalada = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  var aviso = null;
  if (!instalada) {
    if (esIOS) {
      $('instalar').hidden = false;
      $('pasos-ios').hidden = false;
      if (/CriOS|FxiOS|EdgiOS/.test(ua)) $('instalar-texto').textContent = 'Si no ves «Agregar a pantalla de inicio», abre esta página en Safari.';
    }
    window.addEventListener('beforeinstallprompt', function (e) {
      e.preventDefault();
      aviso = e;
      $('instalar').hidden = false;
      $('btn-instalar').hidden = false;
    });
    $('btn-instalar').addEventListener('click', function () {
      if (!aviso) return;
      aviso.prompt();
      aviso.userChoice.then(function () { aviso = null; $('btn-instalar').hidden = true; $('instalar').hidden = true; });
    });
    window.addEventListener('appinstalled', function () { $('instalar').hidden = true; });
  }

  /* ── Service worker y versiones ── */
  if ('serviceWorker' in navigator) {
    var recargando = false, habia = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.addEventListener('controllerchange', function () {
      if (!habia) { habia = true; return; }               // primera instalación: no recargar
      if (!recargando) { recargando = true; location.reload(); }
    });
    navigator.serviceWorker.register('sw.js').then(function (reg) {
      function avisar(w) {
        $('toast').hidden = false;
        $('btn-actualizar').onclick = function () { w.postMessage('actualizar'); };
      }
      if (reg.waiting && navigator.serviceWorker.controller) avisar(reg.waiting);
      reg.addEventListener('updatefound', function () {
        var n = reg.installing;
        if (!n) return;
        n.addEventListener('statechange', function () {
          if (n.state === 'installed' && navigator.serviceWorker.controller) avisar(n);
        });
      });
      setInterval(function () { reg.update().catch(function () {}); }, 60 * 60 * 1000);
    }).catch(function () {});
  }

  arranque();
})();
