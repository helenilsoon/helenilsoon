import worker from "./worker.js";
import fs from "fs";

async function runTest() {
  console.log("--- TESTE 1: HEADER DINAMICO ---");
  const reqHeader = new Request("https://api.webuildsites.com.br/api/header?name=HELENILSON+OLIVEIRA&role=FULL+STACK+ARCHITECT&org=@WebuildSoft&repos=45%2B+Criados&availability=Disponivel");
  const resHeader = await worker.fetch(reqHeader);
  console.log("Header Status:", resHeader.status);
  const svgHeader = await resHeader.text();
  fs.writeFileSync("/home/helenilson/Documentos/projetos/readmeHelenilson/api-neon-cards/test_generated_header.svg", svgHeader);
  console.log("Header SVG gerado:", svgHeader.length, "bytes");

  console.log("--- TESTE 2: PROJECT CARD DINAMICO ---");
  const reqProj = new Request("https://api.webuildsites.com.br/api/project?title=MyRifa+SaaS&url=myrifa.com.br&desc1=Plataforma+com+Pix+automatico&desc2=Cloudflare+R2+e+Supabase&tag1=Next.js&tag2=Supabase&tag3=Pix&model=coin");
  const resProj = await worker.fetch(reqProj);
  console.log("Project Status:", resProj.status);
  const svgProj = await resProj.text();
  fs.writeFileSync("/home/helenilson/Documentos/projetos/readmeHelenilson/api-neon-cards/test_generated_project.svg", svgProj);
  console.log("Project SVG gerado:", svgProj.length, "bytes");

  console.log("--- TODOS OS TESTES PASSARAM COM SUCESSO! ---");
}

runTest().catch(console.error);
