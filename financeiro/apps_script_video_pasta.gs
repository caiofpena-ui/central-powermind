// ─────────────────────────────────────────────────────────────────────────────
// ADICIONAR ao Apps Script existente (script.google.com → seu projeto RM12)
// Cole este bloco DENTRO da função doPost(), no switch/if de "acao":
//
//   if (dados.acao === "criar_pasta_video") { ... }
//
// ─────────────────────────────────────────────────────────────────────────────

// Dentro de doPost(e), adicione este bloco antes do return final:

  if (dados.acao === "criar_pasta_video") {
    try {
      var nomeCreator = dados.nome_creator || dados.username || "Creator";
      var username    = dados.username || "creator";
      var cpf         = dados.cpf || "";

      // Pasta raiz do RM12 — mesma onde fica o Fluxo de Caixa
      // Substitua pelo ID da sua pasta RM12 se souber, ou deixe buscar pelo nome:
      var pastaRaiz = DriveApp.getFoldersByName("RM12").next(); // ajuste se necessário

      // Cria (ou reutiliza) pasta "Vídeos Creators"
      var pastaVideos;
      var itVideos = pastaRaiz.getFoldersByName("Vídeos Creators");
      if (itVideos.hasNext()) {
        pastaVideos = itVideos.next();
      } else {
        pastaVideos = pastaRaiz.createFolder("Vídeos Creators");
      }

      // Cria subpasta exclusiva para o creator: "NomeCreator (@username)"
      var nomePasta = nomeCreator + (username ? " (@" + username + ")" : "");
      var pastaCreator;
      var itCreator = pastaVideos.getFoldersByName(nomePasta);
      if (itCreator.hasNext()) {
        pastaCreator = itCreator.next(); // reutiliza se já existir
      } else {
        pastaCreator = pastaVideos.createFolder(nomePasta);
      }

      // Permissão: qualquer pessoa com o link pode adicionar arquivos
      pastaCreator.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.EDIT);

      var folderUrl = pastaCreator.getUrl();

      return ContentService
        .createTextOutput(JSON.stringify({ ok: true, folder_url: folderUrl }))
        .setMimeType(ContentService.MimeType.JSON);

    } catch (err) {
      return ContentService
        .createTextOutput(JSON.stringify({ ok: false, error: err.toString() }))
        .setMimeType(ContentService.MimeType.JSON);
    }
  }

// ─────────────────────────────────────────────────────────────────────────────
// ESTRUTURA COMPLETA do doPost (para referência):
//
// function doPost(e) {
//   var dados = JSON.parse(e.postData.contents);
//
//   if (dados.acao === "salvar_lancamento") { ... }    // já existe
//   if (dados.acao === "salvar_contrato")   { ... }    // já existe
//   if (dados.acao === "criar_pasta_video") { ... }    // ← NOVO: cole acima
//
//   return ContentService.createTextOutput(JSON.stringify({ok:true}))...
// }
// ─────────────────────────────────────────────────────────────────────────────
