/**
 * Cloudflare Worker API
 * Neon Profile Card Generator API
 * WebuildSoft & Helenilson Oliveira © 2026
 */

function escapeXml(unsafe) {
  if (!unsafe) return "";
  return String(unsafe)
    .slice(0, 80)
    .replace(/[<>&'"]/g, (c) => {
      switch (c) {
        case "<": return "&lt;";
        case ">": return "&gt;";
        case "&": return "&amp;";
        case "\'": return "&apos;";
        case "\"": return "&quot;";
        default: return c;
      }
    });
}

// 1. Header Generator
function renderHeader(params) {
  const name = escapeXml(params.get("name") || "DEV NAME");
  const role = escapeXml(params.get("role") || "FULL STACK DEVELOPER");
  const bio = escapeXml(params.get("bio") || "Building scalable digital solutions and high-performance architectures.");
  const status = escapeXml(params.get("status") || "STATUS: ONLINE • READY TO BUILD");
  const loc = escapeXml(params.get("location") || "REMOTE (UTC-3)");
  const org = escapeXml(params.get("org") || "@WebuildSoft ↗");
  const repos = escapeXml(params.get("repos") || "30+ Repos");
  const avail = escapeXml(params.get("availability") || "Open for Contracts");
  const badge4 = escapeXml(params.get("badge4") || "Full Stack Dev");

  return `<svg width="100%" height="auto" viewBox="0 0 900 280" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="neonGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#22d3ee" /><stop offset="50%" stop-color="#99f6e4" /><stop offset="100%" stop-color="#d946ef" />
    </linearGradient>
    <linearGradient id="cardBorder" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.8" /><stop offset="50%" stop-color="#3b82f6" stop-opacity="0.3" /><stop offset="100%" stop-color="#d946ef" stop-opacity="0.6" />
    </linearGradient>
    <linearGradient id="bgDark" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#07090e" /><stop offset="100%" stop-color="#0c101a" />
    </linearGradient>
    <filter id="neonCometGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3.5" result="blur1" />
      <feMerge><feMergeNode in="blur1" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
    <linearGradient id="neonCometGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f0ff" /><stop offset="30%" stop-color="#3b82f6" /><stop offset="65%" stop-color="#a855f7" /><stop offset="100%" stop-color="#ec4899" />
    </linearGradient>
    <style>
      .title-text { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 900; font-size: 38px; letter-spacing: -0.5px; }
      .mono-text { font-family: 'Fira Code', monospace; }
      .badge-text { font-size: 11px; font-weight: 600; }
      @keyframes pulseDot { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
      .pulse { animation: pulseDot 2s infinite ease-in-out; }
      @keyframes cometRun { 0% { stroke-dashoffset: 2344; } 100% { stroke-dashoffset: 0; } }
      .comet-beam { stroke-dasharray: 280 2064; animation: cometRun 6s linear infinite; pointer-events: none; }
    </style>
  </defs>

  <rect x="2" y="2" width="896" height="276" rx="16" fill="url(#bgDark)" stroke="url(#cardBorder)" stroke-width="1.5" />
  <rect class="comet-beam" x="2" y="2" width="896" height="276" rx="16" fill="none" stroke="url(#neonCometGrad)" stroke-width="2.6" stroke-linecap="round" filter="url(#neonCometGlow)" />

  <circle cx="830" cy="40" r="90" fill="#06b6d4" fill-opacity="0.12" />
  <circle cx="70" cy="240" r="80" fill="#d946ef" fill-opacity="0.08" />

  <!-- TOP BAR -->
  <rect x="36" y="26" width="310" height="26" rx="13" fill="#083344" fill-opacity="0.7" stroke="#06b6d4" stroke-opacity="0.4" stroke-width="1" />
  <circle cx="50" cy="39" r="4.5" fill="#22d3ee" class="pulse" />
  <text x="63" y="43" fill="#67e8f9" class="mono-text badge-text">${status}</text>
  <text x="864" y="43" fill="#f472b6" class="mono-text badge-text" text-anchor="end">${loc}</text>

  <!-- HERO -->
  <text x="36" y="98" fill="url(#neonGradient)" class="title-text">${name}</text>
  <text x="36" y="125" fill="#67e8f9" class="mono-text" font-size="13" font-weight="600">&gt; ${role}</text>
  <text x="36" y="148" fill="#8b949e" class="mono-text" font-size="12">${bio}</text>

  <!-- CHIPS -->
  <g transform="translate(36, 185)">
    <rect width="195" height="64" rx="12" fill="#000000" fill-opacity="0.65" stroke="#06b6d4" stroke-opacity="0.35" stroke-width="1.2" />
    <text x="24" y="30" fill="#22d3ee" class="mono-text" font-size="10" font-weight="bold">ORGANIZAÇÃO</text>
    <text x="24" y="49" fill="#ffffff" class="mono-text" font-size="13" font-weight="bold">${org}</text>
  </g>
  <g transform="translate(245, 185)">
    <rect width="195" height="64" rx="12" fill="#000000" fill-opacity="0.65" stroke="#d946ef" stroke-opacity="0.35" stroke-width="1.2" />
    <text x="24" y="30" fill="#f472b6" class="mono-text" font-size="10" font-weight="bold">REPOSITÓRIOS</text>
    <text x="24" y="49" fill="#ffffff" class="mono-text" font-size="13" font-weight="bold">${repos}</text>
  </g>
  <g transform="translate(454, 185)">
    <rect width="195" height="64" rx="12" fill="#000000" fill-opacity="0.65" stroke="#10b981" stroke-opacity="0.35" stroke-width="1.2" />
    <text x="24" y="30" fill="#34d399" class="mono-text" font-size="10" font-weight="bold">DISPONIBILIDADE</text>
    <text x="24" y="49" fill="#ffffff" class="mono-text" font-size="13" font-weight="bold">${avail}</text>
  </g>
  <g transform="translate(663, 185)">
    <rect width="201" height="64" rx="12" fill="#000000" fill-opacity="0.65" stroke="#c084fc" stroke-opacity="0.35" stroke-width="1.2" />
    <text x="24" y="30" fill="#c084fc" class="mono-text" font-size="10" font-weight="bold">ATUAÇÃO</text>
    <text x="24" y="49" fill="#ffffff" class="mono-text" font-size="13" font-weight="bold">${badge4}</text>
  </g>
</svg>`;
}

// 2. Project Card Generator
function renderProject(params) {
  const title = escapeXml(params.get("title") || "Projeto em Destaque");
  const category = escapeXml(params.get("category") || "PLATAFORMA SAAS");
  const url = escapeXml(params.get("url") || "domain.com.br ↗");
  const desc1 = escapeXml(params.get("desc1") || "Descrição da solução em produção com arquitetura moderna,");
  const desc2 = escapeXml(params.get("desc2") || "alta disponibilidade, testes automatizados e deploy contínuo.");
  const tag1 = escapeXml(params.get("tag1") || "Next.js 14");
  const tag2 = escapeXml(params.get("tag2") || "TypeScript");
  const tag3 = escapeXml(params.get("tag3") || "Docker");
  const modelType = params.get("model") || "coin";

  let modelSvg = "";
  if (modelType === "coin") {
    modelSvg = `
    <g transform="translate(375, 42)">
      <circle cx="0" cy="0" r="18" fill="#ca8a04" stroke="#fef08a" stroke-width="1.2" />
      <polygon points="0,-4 5,0 0,4 -5,0" fill="#064e3b" stroke="#34d399" stroke-width="0.9" />
    </g>`;
  } else {
    modelSvg = `
    <g transform="translate(375, 42)">
      <polygon points="0,-14 15,-6 0,2 -15,-6" fill="#00f0ff" fill-opacity="0.75" stroke="#67e8f9" stroke-width="1" />
      <polygon points="-15,-6 0,2 0,16 -15,8" fill="#0284c7" stroke="#38bdf8" stroke-width="1" />
      <polygon points="0,2 15,-6 15,8 0,16" fill="#0369a1" stroke="#00f0ff" stroke-width="1" />
    </g>`;
  }

  return `<svg width="100%" height="auto" viewBox="0 0 420 146" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cardBorder" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981" stop-opacity="0.8" /><stop offset="100%" stop-color="#047857" stop-opacity="0.3" />
    </linearGradient>
    <style>
      .card-title { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; font-weight: 700; fill: #ffffff; }
      .card-desc { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; fill: #94a3b8; }
      .tag-txt { font-family: 'Fira Code', monospace; font-size: 9px; font-weight: 600; fill: #34d399; }
      .category { font-family: 'Fira Code', monospace; font-size: 10px; font-weight: bold; fill: #34d399; letter-spacing: 0.5px; }
      .arrow { font-family: 'Fira Code', monospace; font-size: 11.5px; fill: #34d399; font-weight: bold; }
    </style>
  </defs>

  <rect x="1.5" y="1.5" width="417" height="143" rx="14" fill="#080c14" stroke="url(#cardBorder)" stroke-width="1.4" />
  <circle cx="375" cy="42" r="32" fill="#10b981" fill-opacity="0.08" />

  <text x="24" y="30" class="category">${category}</text>
  <text x="24" y="44" class="arrow">${url}</text>

  ${modelSvg}

  <text x="20" y="73" class="card-title">${title}</text>
  <text x="20" y="93" class="card-desc">${desc1}</text>
  <text x="20" y="108" class="card-desc">${desc2}</text>

  <g transform="translate(20, 117)">
    <rect width="70" height="20" rx="5" fill="#064e3b" fill-opacity="0.4" stroke="#10b981" stroke-opacity="0.3" />
    <text x="35" y="13.5" text-anchor="middle" class="tag-txt">${tag1}</text>
  </g>
  <g transform="translate(98, 117)">
    <rect width="74" height="20" rx="5" fill="#064e3b" fill-opacity="0.4" stroke="#10b981" stroke-opacity="0.3" />
    <text x="37" y="13.5" text-anchor="middle" class="tag-txt">${tag2}</text>
  </g>
  <g transform="translate(180, 117)">
    <rect width="70" height="20" rx="5" fill="#064e3b" fill-opacity="0.4" stroke="#10b981" stroke-opacity="0.3" />
    <text x="35" y="13.5" text-anchor="middle" class="tag-txt">${tag3}</text>
  </g>
</svg>`;
}

const handler = {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    const params = url.searchParams;

    const headers = {
      "Content-Type": "image/svg+xml; charset=utf-8",
      "Cache-Control": "public, max-age=14400, s-maxage=14400",
      "Access-Control-Allow-Origin": "*",
    };

    if (path === "/api/header" || path === "/header") {
      return new Response(renderHeader(params), { headers });
    }

    if (path === "/api/project" || path === "/project") {
      return new Response(renderProject(params), { headers });
    }

    if (path === "/api/health" || path === "/health") {
      return new Response(JSON.stringify({ status: "online", api: "neon-profile-generator", v: "1.0.0" }), {
        headers: { "Content-Type": "application/json" }
      });
    }

    return new Response(JSON.stringify({
      message: "Neon Profile Card Generator API",
      author: "Helenilson Oliveira • WebuildSoft",
      endpoints: {
        header: "/api/header?name=SEU+NOME&role=FULL+STACK&org=@SUAORG&repos=30%2B+Criados",
        project: "/api/project?title=Meu+Projeto&url=meuapp.com&tag1=React&tag2=Go&tag3=Docker"
      }
    }, null, 2), {
      headers: { "Content-Type": "application/json" }
    });
  }
};

export default handler;

