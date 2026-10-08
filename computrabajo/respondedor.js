// Respondedor de "Preguntas de selección" de Computrabajo.
// Se inyecta en la página /candidate/kq y recibe el objeto de perfil.json.
// Llena solo lo que tiene respuesta segura; si queda alguna pregunta sin respuesta,
// NO envía y devuelve la lista para que Claude (o la persona) la conteste.
(perfil => {
  const art = document.querySelector('article') || document.body;
  const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
  const lab = r => (r.closest('label') || r.parentElement).innerText.trim();
  const salario = perfil.salario_actual || Object.values(perfil.salario || {})[0] || '';

  // Controles en orden del DOM: textareas y grupos de radios
  const controles = [];
  const vistos = new Set();
  art.querySelectorAll('textarea, input[type=radio]').forEach(el => {
    if (el.tagName === 'TEXTAREA') controles.push({ tipo: 'T', el });
    else if (!vistos.has(el.name)) {
      vistos.add(el.name);
      controles.push({ tipo: 'R', opciones: [...art.querySelectorAll(`input[type=radio][name="${CSS.escape(el.name)}"]`)] });
    }
  });
  const etiquetasRadio = new Set(controles.filter(c => c.tipo === 'R').flatMap(c => c.opciones.map(lab)));
  const lineas = art.innerText.split('\n').map(s => s.trim()).filter(Boolean);
  const inicio = lineas.findIndex(l => /contesta estas preguntas/i.test(l));
  const preguntas = lineas.slice(inicio + 1).filter(l => !/^\(m[aá]ximo/i.test(l) && !etiquetasRadio.has(l));

  const textos = [
    [/correo|e-?mail/i, perfil.email],
    [/expedici[oó]n/i, perfil.expedicion],
    [/c[eé]dula|documento de identidad|n[uú]mero de documento/i, perfil.cedula],
    [/eres (t[eé]cnico|tecn[oó]logo)|es (t[eé]cnico|tecn[oó]logo)|cuentas? con (formaci[oó]n|t[ií]tulo)/i, perfil.formacion],
    [/tel[eé]fono|celular|whats|n[uú]mero de contacto/i, perfil.telefono],
    [/talla/i, perfil.tallas],
    [/multa|comparendo/i, perfil.tiene_multas ? null : 'No.'],
    [/ingl[eé]s/i, perfil.ingles],
    [/transporte/i, perfil.transporte],
    [/salari|aspiraci[oó]n|expectativa/i, salario],
    [/formaci[oó]n|estudios|escolaridad|acad[eé]mic|t[ií]tulo/i, perfil.formacion],
    [/d[oó]nde vive|lugar de residencia|reside|barrio|localidad|zona|ciudad/i, perfil.residencia],
    [/edad|a[nñ]os tienes/i, perfil.edad ? String(perfil.edad) : null],
    [/disponib|inmediat|horario|turno|fin(es)? de semana|domingo|temporada|interesa|de acuerdo|acepta/i, perfil.disponibilidad],
  ];
  const radiosSi = /autoriz|acuerdo|disponib|interes|inmediat|horario|turno|presencial/i;
  const nivel = perfil.nivel_estudios_regex ? new RegExp(perfil.nivel_estudios_regex, 'i') : null;

  const faltan = [];
  controles.forEach((c, i) => {
    const q = preguntas[i] || '';
    if (c.tipo === 'T') {
      const hit = textos.find(([re, v]) => re.test(q) && v);
      if (hit) { setter.call(c.el, hit[1]); c.el.dispatchEvent(new Event('input', { bubbles: true })); }
      else faltan.push('T: ' + q);
    } else {
      const op = c.opciones;
      let elegido = null;
      if (/estudias actualmente|estudia actualmente/i.test(q)) elegido = null; // depende de cada persona
      else if (nivel && /escolaridad|nivel (de )?estudio|grado/i.test(q)) elegido = op.find(r => nivel.test(lab(r)));
      else if (radiosSi.test(q) && !/experiencia/i.test(q)) elegido = op.find(r => /^s[ií]/i.test(lab(r)));
      if (elegido) elegido.click(); else faltan.push('R: ' + q + ' [' + op.map(lab).join(' / ') + ']');
    }
  });

  if (faltan.length) return 'PENDIENTE\n' + faltan.join('\n');
  const b = [...document.querySelectorAll('button,input[type=submit]')].find(b => /Enviar mi HdV/.test(b.innerText || b.value));
  setTimeout(() => b.click(), 300);
  return 'ENVIADO (' + controles.length + ' respuestas)';
})
