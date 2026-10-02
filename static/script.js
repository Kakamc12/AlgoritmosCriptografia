"use strict";

const el = {
  lista: document.getElementById("lista-cifras"),
  nome: document.getElementById("nome-cifra"),
  descricao: document.getElementById("descricao-cifra"),
  operacoes: document.getElementById("operacoes"),
  formulario: document.getElementById("formulario"),
  campos: document.getElementById("campos"),
  botao: document.getElementById("botao-executar"),
  saida: document.getElementById("saida"),
  copiar: document.getElementById("botao-copiar"),
  usar: document.getElementById("botao-usar"),
};

let cifras = [];
let cifraAtual = null;
let operacaoAtual = null;
const valores = {}; // valores digitados, guardados por cifra

// ---------------------------------------------------------------------------
// Inicialização
// ---------------------------------------------------------------------------
async function iniciar() {
  try {
    const resposta = await fetch("/api/cifras");
    cifras = await resposta.json();
  } catch (e) {
    mostrarErro("Não foi possível carregar as cifras. O servidor está rodando?");
    return;
  }

  for (const c of cifras) {
    valores[c.id] = {};
    for (const campo of c.campos) valores[c.id][campo.id] = campo.padrao;
  }

  desenharLista();
  selecionarCifra(cifras[0].id);
}

// ---------------------------------------------------------------------------
// Desenho da interface
// ---------------------------------------------------------------------------
function desenharLista() {
  el.lista.innerHTML = "";
  for (const c of cifras) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "item-cifra";
    b.textContent = c.nome;
    b.dataset.id = c.id;
    b.addEventListener("click", () => selecionarCifra(c.id));
    el.lista.appendChild(b);
  }
}

function selecionarCifra(id) {
  cifraAtual = cifras.find((c) => c.id === id);
  operacaoAtual = cifraAtual.operacoes[0].id;

  for (const b of el.lista.children) {
    b.setAttribute("aria-current", b.dataset.id === id ? "true" : "false");
  }

  el.nome.textContent = cifraAtual.nome;
  el.descricao.textContent = cifraAtual.descricao;

  desenharOperacoes();
  desenharCampos();
  limparSaida();
}

function desenharOperacoes() {
  el.operacoes.innerHTML = "";
  for (const op of cifraAtual.operacoes) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "operacao";
    b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", op.id === operacaoAtual ? "true" : "false");
    b.textContent = op.rotulo;
    b.addEventListener("click", () => selecionarOperacao(op.id));
    el.operacoes.appendChild(b);
  }
  atualizarBotao();
}

function selecionarOperacao(id) {
  operacaoAtual = id;
  desenharOperacoes();
  desenharCampos();
  limparSaida();
}

function atualizarBotao() {
  const op = cifraAtual.operacoes.find((o) => o.id === operacaoAtual);
  el.botao.textContent = op.acao;
}

function desenharCampos() {
  el.campos.innerHTML = "";

  for (const campo of cifraAtual.campos) {
    if (campo.ops && !campo.ops.includes(operacaoAtual)) continue;

    const bloco = document.createElement("div");
    bloco.className = "campo";

    const inputId = `campo-${campo.id}`;
    const rotulo = document.createElement("label");
    rotulo.htmlFor = inputId;
    rotulo.textContent = campo.rotulos[operacaoAtual] || campo.rotulo;

    let entrada;
    if (campo.tipo === "textarea") {
      entrada = document.createElement("textarea");
      entrada.rows = campo.id === "matriz" ? 4 : 3;
    } else {
      entrada = document.createElement("input");
      // "number" em <input> bloqueia formatos como 0xACE1; por isso usa texto
      entrada.type = "text";
      if (campo.tipo === "number") entrada.inputMode = "numeric";
    }
    entrada.id = inputId;
    entrada.name = campo.id;
    entrada.spellcheck = false;
    entrada.autocomplete = "off";
    entrada.placeholder = campo.placeholder || "";
    entrada.value = valores[cifraAtual.id][campo.id];
    entrada.addEventListener("input", () => {
      valores[cifraAtual.id][campo.id] = entrada.value;
    });

    bloco.append(rotulo, entrada);

    if (campo.ajuda) {
      const ajuda = document.createElement("p");
      ajuda.className = "ajuda";
      ajuda.textContent = campo.ajuda;
      bloco.appendChild(ajuda);
    }

    el.campos.appendChild(bloco);
  }
}

// ---------------------------------------------------------------------------
// Resultado
// ---------------------------------------------------------------------------
function limparSaida() {
  el.saida.className = "saida-texto vazio";
  el.saida.textContent = "O resultado aparece aqui.";
  el.copiar.hidden = true;
  el.usar.hidden = true;
}

function mostrarResultado(texto) {
  el.saida.className = "saida-texto";
  el.saida.textContent = texto;
  el.copiar.hidden = false;
  el.usar.hidden = !podeReusarResultado();
}

function mostrarErro(mensagem) {
  el.saida.className = "saida-texto erro";
  el.saida.textContent = mensagem;
  el.copiar.hidden = true;
  el.usar.hidden = true;
}

function podeReusarResultado() {
  // Só nas operações cifrar/decifrar, cujo resultado é um texto que serve de entrada
  return (
    (operacaoAtual === "cifrar" || operacaoAtual === "decifrar") &&
    cifraAtual.campos.some((c) => c.id === "texto")
  );
}

// ---------------------------------------------------------------------------
// Execução
// ---------------------------------------------------------------------------
async function executar() {
  el.botao.disabled = true;
  try {
    const resposta = await fetch("/api/executar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cifra: cifraAtual.id,
        operacao: operacaoAtual,
        valores: valores[cifraAtual.id],
      }),
    });
    const dados = await resposta.json();
    if (dados.ok) mostrarResultado(dados.resultado);
    else mostrarErro(dados.erro);
  } catch (e) {
    mostrarErro("Não foi possível falar com o servidor. Ele está rodando?");
  } finally {
    el.botao.disabled = false;
  }
}

el.formulario.addEventListener("submit", (ev) => {
  ev.preventDefault();
  executar();
});

el.formulario.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && (ev.ctrlKey || ev.metaKey)) {
    ev.preventDefault();
    executar();
  }
});

el.copiar.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(el.saida.textContent);
    el.copiar.textContent = "Copiado";
  } catch (e) {
    el.copiar.textContent = "Não foi possível copiar";
  }
  setTimeout(() => (el.copiar.textContent = "Copiar"), 1500);
});

// Leva o resultado para o campo de texto e alterna entre cifrar e decifrar
el.usar.addEventListener("click", () => {
  valores[cifraAtual.id].texto = el.saida.textContent;

  const ids = cifraAtual.operacoes.map((o) => o.id);
  if (operacaoAtual === "cifrar" && ids.includes("decifrar")) operacaoAtual = "decifrar";
  else if (operacaoAtual === "decifrar" && ids.includes("cifrar")) operacaoAtual = "cifrar";

  desenharOperacoes();
  desenharCampos();
  limparSaida();
});

iniciar();
