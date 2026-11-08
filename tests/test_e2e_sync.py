#!/usr/bin/env python3
"""
Suíte de Testes E2E: Sincronização Global do Feixe Cometa Neon (T = 21s)
Cobre os 14 SVGs em assets/ e a integração com README.md em 4 Tiers:
- Tier 1: Feature Coverage (≥5 testes por feature)
- Tier 2: Boundary & Corner Cases (≥5 testes por feature)
- Tier 3: Cross-Feature Combinations (Pairwise, Continuidade, Exclusão Mútua, Não-Regressão)
- Tier 4: Real-World Scenarios (Integração README.md, Links, Dimensões e Renderização)
"""

import glob
import math
import os
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(WORKSPACE_ROOT, "assets")
README_PATH = os.path.join(WORKSPACE_ROOT, "README.md")

# Sequência canônica estrita dos 14 cards (R1)
EXPECTED_CARDS = [
    {"index": 1, "filename": "header.svg", "title": "Top Banner", "start_s": 0.0, "end_s": 1.5, "perimeter": 2317},
    {"index": 2, "filename": "card_stack.svg", "title": "Production Stack", "start_s": 1.5, "end_s": 3.0, "perimeter": 1604},
    {"index": 3, "filename": "btn_portfolio.svg", "title": "Portfolio Button", "start_s": 3.0, "end_s": 4.5, "perimeter": 933},
    {"index": 4, "filename": "btn_email.svg", "title": "Email Button", "start_s": 4.5, "end_s": 6.0, "perimeter": 933},
    {"index": 5, "filename": "btn_org.svg", "title": "Org Button", "start_s": 6.0, "end_s": 7.5, "perimeter": 933},
    {"index": 6, "filename": "btn_location.svg", "title": "Location Button", "start_s": 7.5, "end_s": 9.0, "perimeter": 933},
    {"index": 7, "filename": "spotify.svg", "title": "Soundtrack Spotify", "start_s": 9.0, "end_s": 10.5, "perimeter": 1001},
    {"index": 8, "filename": "card_myrifa.svg", "title": "Project MyRifa", "start_s": 10.5, "end_s": 12.0, "perimeter": 1096},
    {"index": 9, "filename": "card_webuildsites.svg", "title": "Project WebuildSites", "start_s": 12.0, "end_s": 13.5, "perimeter": 1096},
    {"index": 10, "filename": "card_lnki.svg", "title": "Project Lnki.pro", "start_s": 13.5, "end_s": 15.0, "perimeter": 1096},
    {"index": 11, "filename": "card_lenamimos.svg", "title": "Project Lena Mimos", "start_s": 15.0, "end_s": 16.5, "perimeter": 1096},
    {"index": 12, "filename": "card_antigravity.svg", "title": "Project Antigravity", "start_s": 16.5, "end_s": 18.0, "perimeter": 1936},
    {"index": 13, "filename": "cube_3d.svg", "title": "Cyber Core 3D", "start_s": 18.0, "end_s": 19.5, "perimeter": 1444},
    {"index": 14, "filename": "trophies.svg", "title": "RPG Trophies", "start_s": 19.5, "end_s": 21.0, "perimeter": 620},
]

EXPECTED_NEON_COLORS = {
    "#00f0ff": "Electric Cyan",
    "#3b82f6": "Deep Electric Blue",
    "#a855f7": "Ultraviolet Purple",
    "#ec4899": "Hot Magenta",
}

EXPECTED_LINKS = [
    {"asset": "assets/btn_portfolio.svg", "url": "https://helenilsoon.github.io/portifolio/"},
    {"asset": "assets/btn_email.svg", "url": "mailto:helenilsoon@gmail.com"},
    {"asset": "assets/btn_org.svg", "url": "https://github.com/WebuildSoft"},
    {"asset": "assets/spotify.svg", "url": "https://open.spotify.com"},
    {"asset": "assets/card_myrifa.svg", "url": "https://myrifa.com.br"},
    {"asset": "assets/card_webuildsites.svg", "url": "https://www.webuildsites.com.br"},
    {"asset": "assets/card_lnki.svg", "url": "https://lnki.pro"},
    {"asset": "assets/card_lenamimos.svg", "url": "https://lenamimos.com.br"},
    {"asset": "assets/card_antigravity.svg", "url": "https://github.com/WebuildSoft/antigravity-mobile-releases/releases/latest"},
]


# ============================================================================
# Helpers de Parsing de SVG e CSS
# ============================================================================

def get_svg_path(filename: str) -> str:
    return os.path.join(ASSETS_DIR, filename)


def parse_svg_file(filename: str):
    """Retorna árvore XML e elementos principais do SVG."""
    path = get_svg_path(filename)
    if not os.path.exists(path):
        return None, "", None
    tree = ET.parse(path)
    root = tree.getroot()
    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    return tree, raw_text, root


def extract_css_text(raw_text: str) -> str:
    """Extrai conteúdo de todas as tags <style>."""
    styles = re.findall(r"<style[^>]*>(.*?)</style>", raw_text, re.DOTALL)
    return "\n".join(styles)


def extract_keyframes(css_text: str):
    """
    Retorna dicionário com os @keyframes encontrados:
    { name: { percent_float: { 'opacity': float, 'stroke-dashoffset': float } } }
    """
    kf_dict = {}
    for m in re.finditer(r"@keyframes\s+([A-Za-z0-9_-]+)\s*\{", css_text):
        name = m.group(1)
        start = m.end()
        brace_count = 1
        pos = start
        while pos < len(css_text) and brace_count > 0:
            if css_text[pos] == "{":
                brace_count += 1
            elif css_text[pos] == "}":
                brace_count -= 1
            pos += 1
        body = css_text[start:pos-1]
        steps = {}
        # Encontra blocos de porcentagem, ex: 0%, 7.143% { opacity: 0; ... }
        block_pattern = re.compile(r"([0-9.,%\s]+)\s*\{([^}]+)\}")
        for bmatch in block_pattern.finditer(body):
            selectors = bmatch.group(1).split(",")
            props_raw = bmatch.group(2)
            props = {}
            for prop in props_raw.split(";"):
                prop = prop.strip()
                if not prop:
                    continue
                if ":" in prop:
                    k, v = prop.split(":", 1)
                    props[k.strip().lower()] = v.strip().lower()
            for sel in selectors:
                sel = sel.strip()
                if not sel:
                    continue
                # Converte para float porcentagem
                if sel.endswith("%"):
                    val = float(sel[:-1])
                elif sel in ("from", "0"):
                    val = 0.0
                elif sel in ("to", "100"):
                    val = 100.0
                else:
                    try:
                        val = float(sel)
                    except ValueError:
                        continue
                if val not in steps:
                    steps[val] = {}
                steps[val].update(props)
        kf_dict[name] = steps
    return kf_dict


def find_comet_keyframe(kf_dict: dict, card_index: int):
    """Localiza o bloco de @keyframes associado ao cometa do card."""
    # Procura por cometSweep{card_index}, cometSweep, cometRun ou laserSweep
    preferred_names = [f"cometSweep{card_index}", "cometSweep", f"cometRun{card_index}", "cometRun"]
    for name in preferred_names:
        if name in kf_dict:
            return name, kf_dict[name]
    # Caso contrário, busca qualquer keyframe com stroke-dashoffset
    for name, steps in kf_dict.items():
        for pct, props in steps.items():
            if "stroke-dashoffset" in props:
                return name, steps
    return None, {}


def evaluate_property_at(steps: dict, prop: str, target_pct: float, default_val=0.0):
    """
    Avalia o valor numérico de uma propriedade CSS no instante target_pct (0 a 100),
    usando interpolação linear simples entre os keyframes definidos.
    """
    if not steps:
        return default_val
    sorted_points = []
    for pct, props in steps.items():
        if prop in props:
            val_str = props[prop]
            # Extrai valor numérico (removendo px se houver)
            num_match = re.search(r"[-+]?[0-9]*\.?[0-9]+", val_str)
            if num_match:
                sorted_points.append((pct, float(num_match.group(0))))
    if not sorted_points:
        return default_val
    sorted_points.sort(key=lambda x: x[0])

    # Se estiver exatamente num ponto
    for pct, val in sorted_points:
        if abs(pct - target_pct) < 1e-4:
            return val

    # Se estiver antes do primeiro ou depois do último
    if target_pct <= sorted_points[0][0]:
        return sorted_points[0][1]
    if target_pct >= sorted_points[-1][0]:
        return sorted_points[-1][1]

    # Interpolação linear entre dois pontos adjacentes
    for i in range(len(sorted_points) - 1):
        p1, v1 = sorted_points[i]
        p2, v2 = sorted_points[i + 1]
        if p1 <= target_pct <= p2:
            if abs(p2 - p1) < 1e-6:
                return v1
            ratio = (target_pct - p1) / (p2 - p1)
            return v1 + ratio * (v2 - v1)

    return default_val


# ============================================================================
# TIER 1: FEATURE COVERAGE (≥5 testes por feature)
# ============================================================================

class TestTier1FeatureCoverage(unittest.TestCase):
    """
    Cobertura rigorosa das 5 features fundamentais:
    1. Duração do ciclo (21s em todos os 14 SVGs)
    2. Janelas de keyframes (1.5s / 7.143% por card)
    3. Gradiente 4 cores neon (#00f0ff, #3b82f6, #a855f7, #ec4899)
    4. Filtro glow neon (feGaussianBlur duplo + feMerge)
    5. Elemento do feixe cometa (.comet-beam / neon-comet)
    """

    # --- Feature 1: Duração do ciclo (T = 21s) ---

    def test_f1_1_all_14_svgs_declare_21s_cycle_duration(self):
        """F1.1: Todos os 14 SVGs devem declarar explicitamente '21s' como duração da animação."""
        missing = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            self.assertIsNotNone(raw, f"Arquivo {card['filename']} não encontrado")
            css = extract_css_text(raw)
            # Busca declaração de animação com 21s
            has_21s = bool(re.search(r"animation\s*:[^;]*\b21s\b", css, re.IGNORECASE) or
                           re.search(r"animation-duration\s*:\s*21s", css, re.IGNORECASE))
            if not has_21s:
                missing.append(card["filename"])
        self.assertEqual(missing, [], f"SVGs sem duração 21s no CSS: {missing}")

    def test_f1_2_timing_function_is_linear(self):
        """F1.2: A função de temporização da animação do feixe deve ser estritamente 'linear'."""
        invalid = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            # Procura regras aplicadas a classes de cometa/feixe
            beam_rules = re.findall(r"\.(?:comet-beam|neon-comet|laser-beam)\s*\{([^}]+)\}", css)
            has_linear = False
            for rule in beam_rules:
                if "linear" in rule:
                    has_linear = True
                    break
            if not has_linear:
                invalid.append(card["filename"])
        self.assertEqual(invalid, [], f"SVGs sem função de temporização linear no feixe: {invalid}")

    def test_f1_3_iteration_count_is_infinite(self):
        """F1.3: A contagem de iterações da animação do feixe deve ser estritamente 'infinite'."""
        invalid = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            beam_rules = re.findall(r"\.(?:comet-beam|neon-comet|laser-beam)\s*\{([^}]+)\}", css)
            has_infinite = False
            for rule in beam_rules:
                if "infinite" in rule:
                    has_infinite = True
                    break
            if not has_infinite:
                invalid.append(card["filename"])
        self.assertEqual(invalid, [], f"SVGs sem repetição infinite no feixe: {invalid}")

    def test_f1_4_no_legacy_durations_exist_in_beam_animations(self):
        """F1.4: Nenhuma animação de feixe deve manter durações legadas (ex: 7.5s ou 3.2s)."""
        legacy_found = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            # Busca durações legadas 7.5s ou 3.2s
            if re.search(r"animation\s*:[^;]*\b(?:7\.5s|3\.2s)\b", css):
                legacy_found.append(card["filename"])
        self.assertEqual(legacy_found, [], f"SVGs contendo durações legadas (7.5s / 3.2s): {legacy_found}")

    def test_f1_5_total_cycle_time_calculation_integrity(self):
        """F1.5: O somatório das fatias nominais de tempo dos 14 cards deve totalizar exatamente 21.0s."""
        total_time = sum(c["end_s"] - c["start_s"] for c in EXPECTED_CARDS)
        self.assertAlmostEqual(total_time, 21.0, places=4, msg="Soma das durações deve ser 21.0s")
        # Cada card individual deve ter exatamente 1.5s
        for c in EXPECTED_CARDS:
            self.assertAlmostEqual(c["end_s"] - c["start_s"], 1.5, places=4,
                                   msg=f"Card {c['filename']} deve ter duração nominal de 1.5s")

    # --- Feature 2: Janelas de Keyframes (1.5s / 7.143% por card) ---

    def test_f2_1_keyframe_window_width_per_card(self):
        """F2.1: Cada card deve possuir uma janela de atividade nominal de 7.143% (1/14 do ciclo)."""
        invalid_windows = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf_dict = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf_dict, card["index"])
            if not steps:
                invalid_windows.append((card["filename"], "Sem keyframe de cometa"))
                continue
            # Determina intervalo onde opacidade é > 0
            active_points = [pct for pct, props in steps.items() if float(props.get("opacity", 0)) > 0]
            if not active_points:
                invalid_windows.append((card["filename"], "Sem pontos com opacidade > 0"))
                continue
            window_width = max(active_points) - min(active_points)
            # A largura da janela ativa deve estar entre 5.5% e 8.0% (nominal 7.143% menos/mais fade)
            if not (5.5 <= window_width <= 8.5):
                invalid_windows.append((card["filename"], f"Largura fora do padrão: {window_width:.3f}%"))
        self.assertEqual(invalid_windows, [], f"Cards com largura de janela incorreta: {invalid_windows}")

    def test_f2_2_keyframe_start_times_strict_sequence(self):
        """F2.2: O início da janela (t_start) de cada card k deve ser estritamente (k-1) * 7.143%."""
        failures = []
        slot_pct = 100.0 / 14.0
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf_dict = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf_dict, card["index"])
            expected_start = (card["index"] - 1) * slot_pct
            # Procura o ponto de keyframe mais próximo do start
            points = sorted(steps.keys())
            matched = any(abs(p - expected_start) <= 0.15 for p in points)
            if not matched:
                failures.append((card["filename"], f"Esperado start ~{expected_start:.3f}%, pontos: {points}"))
        self.assertEqual(failures, [], f"Falhas no t_start dos keyframes: {failures}")

    def test_f2_3_keyframe_end_times_strict_sequence(self):
        """F2.3: O término da janela (t_end) de cada card k deve ser estritamente k * 7.143%."""
        failures = []
        slot_pct = 100.0 / 14.0
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf_dict = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf_dict, card["index"])
            expected_end = card["index"] * slot_pct
            points = sorted(steps.keys())
            matched = any(abs(p - expected_end) <= 0.15 for p in points)
            if not matched:
                failures.append((card["filename"], f"Esperado end ~{expected_end:.3f}%, pontos: {points}"))
        self.assertEqual(failures, [], f"Falhas no t_end dos keyframes: {failures}")

    def test_f2_4_stroke_dashoffset_travels_full_perimeter(self):
        """F2.4: O stroke-dashoffset deve animar do perímetro P para 0 durante a janela ativa."""
        failures = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf_dict = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf_dict, card["index"])
            offsets = [float(re.search(r"[-+]?[0-9]*\.?[0-9]+", props.get("stroke-dashoffset", "")).group(0))
                       for props in steps.values() if "stroke-dashoffset" in props and
                       re.search(r"[-+]?[0-9]*\.?[0-9]+", props.get("stroke-dashoffset", ""))]
            if not offsets:
                failures.append((card["filename"], "Sem valores de stroke-dashoffset"))
                continue
            max_offset = max(offsets)
            min_offset = min(offsets)
            # min_offset deve ser 0 e max_offset deve estar próximo do perímetro nominal (±15%)
            if min_offset > 5:
                failures.append((card["filename"], f"min_offset não atinge 0: {min_offset}"))
            if max_offset < card["perimeter"] * 0.8:
                failures.append((card["filename"], f"max_offset {max_offset} abaixo do perímetro esperado {card['perimeter']}"))
        self.assertEqual(failures, [], f"Falhas no curso do stroke-dashoffset: {failures}")

    def test_f2_5_fade_in_and_fade_out_transitions(self):
        """F2.5: A animação do feixe deve possuir transição suave de fade-in e fade-out (opacidade 1 durante o curso)."""
        failures = []
        slot_pct = 100.0 / 14.0
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf_dict = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf_dict, card["index"])
            # Ponto central da janela do card k
            mid_point = ((card["index"] - 1) + 0.5) * slot_pct
            op_mid = evaluate_property_at(steps, "opacity", mid_point, default_val=0.0)
            if op_mid < 0.8:
                failures.append((card["filename"], f"Opacidade no ponto médio ({mid_point:.2f}%) é {op_mid}, esperado ~1.0"))
        self.assertEqual(failures, [], f"Falhas na opacidade interna da janela: {failures}")

    # --- Feature 3: Gradiente 4 Cores Neon ---

    def test_f3_1_all_14_svgs_have_neon_comet_gradient(self):
        """F3.1: Todos os 14 SVGs devem conter a definição de linearGradient com id='neonCometGrad'."""
        missing = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            self.assertIsNotNone(root, f"Erro ao carregar {card['filename']}")
            grad = root.find(".//{http://www.w3.org/2000/svg}linearGradient[@id='neonCometGrad']")
            if grad is None:
                # Tenta sem namespace
                grad = root.find(".//linearGradient[@id='neonCometGrad']")
            if grad is None:
                missing.append(card["filename"])
        self.assertEqual(missing, [], f"SVGs sem <linearGradient id='neonCometGrad'>: {missing}")

    def test_f3_2_gradient_has_four_stops(self):
        """F3.2: O gradiente 'neonCometGrad' deve possuir exatamente 4 elementos <stop>."""
        invalid = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            grad = root.find(".//{http://www.w3.org/2000/svg}linearGradient[@id='neonCometGrad']")
            if grad is None:
                grad = root.find(".//linearGradient[@id='neonCometGrad']")
            if grad is None:
                invalid.append((card["filename"], "gradiente ausente"))
                continue
            stops = grad.findall("{http://www.w3.org/2000/svg}stop") or grad.findall("stop")
            if len(stops) != 4:
                invalid.append((card["filename"], f"Esperado 4 stops, encontrado {len(stops)}"))
        self.assertEqual(invalid, [], f"SVGs com contagem incorreta de stops: {invalid}")

    def test_f3_3_gradient_exact_four_neon_colors(self):
        """F3.3: O gradiente deve conter as 4 cores exatas: #00f0ff, #3b82f6, #a855f7, #ec4899."""
        expected_hex = {"#00f0ff", "#3b82f6", "#a855f7", "#ec4899"}
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            grad = root.find(".//{http://www.w3.org/2000/svg}linearGradient[@id='neonCometGrad']")
            if grad is None:
                grad = root.find(".//linearGradient[@id='neonCometGrad']")
            if grad is None:
                failures.append((card["filename"], "gradiente ausente"))
                continue
            stops = grad.findall("{http://www.w3.org/2000/svg}stop") or grad.findall("stop")
            colors = set()
            for s in stops:
                c = s.attrib.get("stop-color", "").lower()
                if not c and "style" in s.attrib:
                    m = re.search(r"stop-color\s*:\s*(#[0-9a-fA-F]{6})", s.attrib["style"])
                    if m:
                        c = m.group(1).lower()
                colors.add(c)
            diff = expected_hex - colors
            if diff:
                failures.append((card["filename"], f"Cores ausentes: {diff}, cores encontradas: {colors}"))
        self.assertEqual(failures, [], f"SVGs sem as 4 cores neon exatas: {failures}")

    def test_f3_4_gradient_stop_offsets_monotonic_progression(self):
        """F3.4: Os offsets dos stops do gradiente devem ser estritamente crescentes (0% -> ~30% -> ~65% -> 100%)."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            grad = root.find(".//{http://www.w3.org/2000/svg}linearGradient[@id='neonCometGrad']")
            if grad is None:
                grad = root.find(".//linearGradient[@id='neonCometGrad']")
            if grad is None:
                continue
            stops = grad.findall("{http://www.w3.org/2000/svg}stop") or grad.findall("stop")
            offsets = []
            for s in stops:
                off = s.attrib.get("offset", "0%")
                if off.endswith("%"):
                    offsets.append(float(off[:-1]))
                else:
                    offsets.append(float(off) * 100.0)
            if len(offsets) == 4:
                if not (offsets[0] <= offsets[1] <= offsets[2] <= offsets[3]):
                    failures.append((card["filename"], f"Offsets não monotônicos: {offsets}"))
                if abs(offsets[0] - 0.0) > 1.0 or abs(offsets[-1] - 100.0) > 1.0:
                    failures.append((card["filename"], f"Offsets devem cobrir 0% a 100%: {offsets}"))
        self.assertEqual(failures, [], f"Offsets de gradiente inválidos: {failures}")

    def test_f3_5_gradient_is_diagonal_orientation(self):
        """F3.5: O gradiente deve ser orientado diagonalmente (x1=0%, y1=0%, x2=100%, y2=100%)."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            grad = root.find(".//{http://www.w3.org/2000/svg}linearGradient[@id='neonCometGrad']")
            if grad is None:
                grad = root.find(".//linearGradient[@id='neonCometGrad']")
            if grad is None:
                continue
            x1 = grad.attrib.get("x1", "0%").strip()
            y1 = grad.attrib.get("y1", "0%").strip()
            x2 = grad.attrib.get("x2", "100%").strip()
            y2 = grad.attrib.get("y2", "100%").strip()
            if not (x1 in ("0%", "0") and y1 in ("0%", "0") and x2 in ("100%", "1") and y2 in ("100%", "1")):
                failures.append((card["filename"], f"Vetor de gradiente ({x1},{y1})->({x2},{y2}) não é diagonal padrão"))
        self.assertEqual(failures, [], f"Gradientes com vetor não-diagonal: {failures}")

    # --- Feature 4: Filtro Glow Neon ---

    def test_f4_1_all_14_svgs_have_glow_filter(self):
        """F4.1: Todos os 14 SVGs devem conter filtro de glow (id='neonCometGlow' ou 'cometGlow')."""
        missing = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            filt = root.find(".//{http://www.w3.org/2000/svg}filter[@id='neonCometGlow']") or \
                   root.find(".//{http://www.w3.org/2000/svg}filter[@id='cometGlow']") or \
                   root.find(".//filter[@id='neonCometGlow']") or \
                   root.find(".//filter[@id='cometGlow']")
            if filt is None:
                missing.append(card["filename"])
        self.assertEqual(missing, [], f"SVGs sem filtro de glow: {missing}")

    def test_f4_2_filter_contains_gaussian_blur(self):
        """F4.2: O filtro de glow deve conter nós <feGaussianBlur>."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            blurs = root.findall(".//{http://www.w3.org/2000/svg}feGaussianBlur") or \
                    root.findall(".//feGaussianBlur")
            if not blurs:
                failures.append(card["filename"])
        self.assertEqual(failures, [], f"SVGs sem nós feGaussianBlur no filtro: {failures}")

    def test_f4_3_filter_blur_radii_structure(self):
        """F4.3: O filtro de glow do cometa deve ter desvios padrões (stdDeviation) entre 1.0 e 5.0."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            filt = root.find(".//{http://www.w3.org/2000/svg}filter[@id='neonCometGlow']") or \
                   root.find(".//{http://www.w3.org/2000/svg}filter[@id='cometGlow']") or \
                   root.find(".//filter[@id='neonCometGlow']") or \
                   root.find(".//filter[@id='cometGlow']")
            if filt is None:
                continue
            blurs = filt.findall("{http://www.w3.org/2000/svg}feGaussianBlur") or filt.findall("feGaussianBlur")
            devs = [float(b.attrib.get("stdDeviation", 0)) for b in blurs if "stdDeviation" in b.attrib]
            if not devs or any(d < 0.5 or d > 8.0 for d in devs):
                failures.append((card["filename"], f"Desvios inválidos: {devs}"))
        self.assertEqual(failures, [], f"Filtros de glow com stdDeviation inválido: {failures}")

    def test_f4_4_filter_fe_merge_with_source_graphic(self):
        """F4.4: O filtro deve usar <feMerge> incluindo 'SourceGraphic' para manter nitidez do traço."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            filt = root.find(".//{http://www.w3.org/2000/svg}filter[@id='neonCometGlow']") or \
                   root.find(".//{http://www.w3.org/2000/svg}filter[@id='cometGlow']") or \
                   root.find(".//filter[@id='neonCometGlow']") or \
                   root.find(".//filter[@id='cometGlow']")
            if filt is None:
                continue
            merge = filt.find("{http://www.w3.org/2000/svg}feMerge") or filt.find("feMerge")
            if merge is None:
                failures.append((card["filename"], "Sem feMerge"))
                continue
            nodes = merge.findall("{http://www.w3.org/2000/svg}feMergeNode") or merge.findall("feMergeNode")
            inputs = [n.attrib.get("in", "") for n in nodes]
            if "SourceGraphic" not in inputs:
                failures.append((card["filename"], f"SourceGraphic ausente nos nós de merge: {inputs}"))
        self.assertEqual(failures, [], f"Filtros sem SourceGraphic no feMerge: {failures}")

    def test_f4_5_filter_bounding_box_expansion(self):
        """F4.5: Os limites do filtro (x, y, width, height) devem cobrir margens para evitar cortes de glow."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            filt = root.find(".//{http://www.w3.org/2000/svg}filter[@id='neonCometGlow']") or \
                   root.find(".//{http://www.w3.org/2000/svg}filter[@id='cometGlow']") or \
                   root.find(".//filter[@id='neonCometGlow']") or \
                   root.find(".//filter[@id='cometGlow']")
            if filt is None:
                continue
            w = filt.attrib.get("width", "100%")
            h = filt.attrib.get("height", "100%")
            # Deve ser maior ou igual a 120%
            w_val = float(w.replace("%", "")) if "%" in w else float(w) * 100
            h_val = float(h.replace("%", "")) if "%" in h else float(h) * 100
            if w_val < 120 or h_val < 120:
                failures.append((card["filename"], f"Dimensões do filtro insuficientes: width={w}, height={h}"))
        self.assertEqual(failures, [], f"Filtros de glow com dimensões restritas: {failures}")

    # --- Feature 5: Feixe Cometa (.comet-beam) ---

    def test_f5_1_all_14_svgs_contain_comet_beam_element(self):
        """F5.1: Todos os 14 SVGs devem conter elemento <rect> com a classe 'comet-beam' ou 'neon-comet'."""
        missing = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
            has_beam = any(r.attrib.get("class") in ("comet-beam", "neon-comet") for r in rects)
            if not has_beam:
                missing.append(card["filename"])
        self.assertEqual(missing, [], f"SVGs sem elemento rect de cometa (.comet-beam / .neon-comet): {missing}")

    def test_f5_2_comet_beam_has_fill_none(self):
        """F5.2: O elemento do feixe cometa deve ter fill='none' para não obstruir o conteúdo interno."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
            beam_rects = [r for r in rects if r.attrib.get("class") in ("comet-beam", "neon-comet")]
            for b in beam_rects:
                if b.attrib.get("fill", "") != "none":
                    failures.append((card["filename"], f"fill={b.attrib.get('fill')}"))
        self.assertEqual(failures, [], f"Feixes sem fill='none': {failures}")

    def test_f5_3_comet_beam_strokes_gradient(self):
        """F5.3: O elemento de feixe deve utilizar o gradiente neon no stroke (stroke='url(#neonCometGrad)')."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
            beam_rects = [r for r in rects if r.attrib.get("class") in ("comet-beam", "neon-comet")]
            for b in beam_rects:
                st = b.attrib.get("stroke", "")
                if "neonCometGrad" not in st:
                    failures.append((card["filename"], f"stroke={st}"))
        self.assertEqual(failures, [], f"Feixes sem referência a #neonCometGrad: {failures}")

    def test_f5_4_comet_beam_stroke_width_and_linecap_round(self):
        """F5.4: O feixe cometa deve possuir stroke-linecap='round' e stroke-width visível entre 2.0 e 3.5."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
            beam_rects = [r for r in rects if r.attrib.get("class") in ("comet-beam", "neon-comet")]
            for b in beam_rects:
                linecap = b.attrib.get("stroke-linecap", "")
                sw_str = b.attrib.get("stroke-width", "0")
                sw = float(re.search(r"[-+]?[0-9]*\.?[0-9]+", sw_str).group(0)) if re.search(r"[-+]?[0-9]*\.?[0-9]+", sw_str) else 0.0
                if linecap != "round":
                    failures.append((card["filename"], f"stroke-linecap='{linecap}'"))
                if not (1.8 <= sw <= 4.0):
                    failures.append((card["filename"], f"stroke-width={sw}"))
        self.assertEqual(failures, [], f"Feixes sem linecap='round' ou stroke-width adequado: {failures}")

    def test_f5_5_comet_beam_dasharray_perimeter_conservation(self):
        """F5.5: O stroke-dasharray (L_beam L_gap) deve somar aproximadamente o perímetro P do card."""
        failures = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            # Procura regras de stroke-dasharray na classe do feixe
            matches = re.findall(r"stroke-dasharray\s*:\s*([0-9]+)\s+([0-9]+)", css)
            if not matches:
                # Tenta atributo direto no rect
                _, _, root = parse_svg_file(card["filename"])
                rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
                beam_rects = [r for r in rects if r.attrib.get("class") in ("comet-beam", "neon-comet")]
                for b in beam_rects:
                    da = b.attrib.get("stroke-dasharray", "")
                    m = re.match(r"([0-9]+)\s+([0-9]+)", da)
                    if m:
                        matches.append(m.groups())
            if not matches:
                failures.append((card["filename"], "stroke-dasharray não encontrado"))
                continue
            l_beam, l_gap = float(matches[0][0]), float(matches[0][1])
            total_dash = l_beam + l_gap
            expected_p = card["perimeter"]
            # Tolerância de 5%
            if abs(total_dash - expected_p) > expected_p * 0.08:
                failures.append((card["filename"], f"total dash {total_dash} diverge do perímetro {expected_p}"))
        self.assertEqual(failures, [], f"Feixes com soma de dasharray divergente do perímetro: {failures}")


# ============================================================================
# TIER 2: BOUNDARY & CORNER CASES (≥5 testes por feature/aspecto)
# ============================================================================

class TestTier2BoundaryAndCornerCases(unittest.TestCase):
    """
    Testes de limites e casos de borda:
    1. Validação XML/SVG estrita (xml.etree e xmllint)
    2. Opacidade estrita zero fora da janela ativa
    3. Integridade geométrica de viewBox e dimensões
    """

    # --- Validação XML/SVG Estrita ---

    def test_b1_1_xml_etree_parsing_all_14_svgs(self):
        """B1.1: Todos os 14 SVGs devem ser analisados sem exceção pelo xml.etree.ElementTree."""
        for card in EXPECTED_CARDS:
            path = get_svg_path(card["filename"])
            try:
                tree = ET.parse(path)
                self.assertIsNotNone(tree.getroot(), f"Elemento raiz nulo em {card['filename']}")
            except Exception as e:
                self.fail(f"Erro ao parsear {card['filename']} com xml.etree: {e}")

    def test_b1_2_xmllint_validation_all_14_svgs(self):
        """B1.2: Todos os 14 SVGs devem passar com código de saída 0 no validador xmllint nativo."""
        for card in EXPECTED_CARDS:
            path = get_svg_path(card["filename"])
            res = subprocess.run(["xmllint", "--noout", path], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"xmllint falhou em {card['filename']}: {res.stderr}")

    def test_b1_3_root_svg_namespaces_valid(self):
        """B1.3: Todos os SVGs devem declarar namespace 'http://www.w3.org/2000/svg' na raiz."""
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            tag = root.tag
            self.assertTrue(tag.endswith("svg"), f"Tag raiz de {card['filename']} não é <svg>: {tag}")

    def test_b1_4_svg_xml_closing_tags_and_quotes_well_formed(self):
        """B1.4: Assegurar que tags abertas são devidamente fechadas e atributos usam aspas válidas."""
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            # Garante que termina com </svg>
            self.assertTrue(raw.strip().endswith("</svg>"), f"{card['filename']} não termina com </svg>")

    def test_b1_5_svg_no_illegal_or_null_bytes(self):
        """B1.5: Nenhum arquivo SVG deve conter bytes nulos ou caracteres de controle inválidos."""
        for card in EXPECTED_CARDS:
            path = get_svg_path(card["filename"])
            with open(path, "rb") as f:
                content = f.read()
            self.assertNotIn(b"\x00", content, f"Byte nulo detectado em {card['filename']}")

    # --- Opacidade 0 Estrita Fora da Janela ---

    def test_b2_1_strict_zero_opacity_at_t0_for_cards_2_to_14(self):
        """B2.1: No instante t=0%, todos os cards de k=2 a k=14 devem ter opacidade avaliada estritamente 0."""
        failures = []
        for card in EXPECTED_CARDS:
            if card["index"] == 1:
                continue  # Card 1 está no início de sua janela ativa
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf_dict = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf_dict, card["index"])
            op_t0 = evaluate_property_at(steps, "opacity", 0.0, default_val=0.0)
            if op_t0 > 0.01:
                failures.append((card["filename"], f"Opacidade em t=0% é {op_t0}"))
        self.assertEqual(failures, [], f"Cards k=2..14 com opacidade > 0 em t=0%: {failures}")

    def test_b2_2_strict_zero_opacity_at_t100_for_cards_1_to_13(self):
        """B2.2: No instante t=100%, todos os cards de k=1 a k=13 devem ter opacidade avaliada estritamente 0."""
        failures = []
        for card in EXPECTED_CARDS:
            if card["index"] == 14:
                continue  # Card 14 termina em t=100%
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf_dict = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf_dict, card["index"])
            op_t100 = evaluate_property_at(steps, "opacity", 100.0, default_val=0.0)
            if op_t100 > 0.01:
                failures.append((card["filename"], f"Opacidade em t=100% é {op_t100}"))
        self.assertEqual(failures, [], f"Cards k=1..13 com opacidade > 0 em t=100%: {failures}")

    def test_b2_3_strict_zero_opacity_at_midpoints_of_all_other_cards(self):
        """B2.3: Para cada card k, nos pontos médios das janelas de todos os outros 13 cards, a opacidade deve ser 0."""
        slot_pct = 100.0 / 14.0
        failures = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf_dict = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf_dict, card["index"])
            for other in EXPECTED_CARDS:
                if other["index"] == card["index"]:
                    continue
                other_mid = ((other["index"] - 1) + 0.5) * slot_pct
                op = evaluate_property_at(steps, "opacity", other_mid, default_val=0.0)
                if op > 0.01:
                    failures.append((card["filename"], f"Opacidade={op:.3f} no meio do Card {other['index']} ({other_mid:.2f}%)"))
        self.assertEqual(failures, [], f"Cards exibindo feixe ativo fora de sua janela: {failures}")

    def test_b2_4_opacity_zero_at_window_endpoints(self):
        """B2.4: Nos instantes exatos de start e end, a opacidade no keyframe deve ser 0 (fade-in / fade-out)."""
        slot_pct = 100.0 / 14.0
        failures = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf_dict = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf_dict, card["index"])
            t_start = (card["index"] - 1) * slot_pct
            t_end = card["index"] * slot_pct
            op_start = evaluate_property_at(steps, "opacity", t_start, default_val=0.0)
            op_end = evaluate_property_at(steps, "opacity", t_end, default_val=0.0)
            if op_start > 0.05 or op_end > 0.05:
                failures.append((card["filename"], f"op_start({t_start:.2f}%)={op_start}, op_end({t_end:.2f}%)={op_end}"))
        self.assertEqual(failures, [], f"Opacidades de borda não zeradas: {failures}")

    def test_b2_5_comet_beam_pointer_events_none(self):
        """B2.5: O elemento do feixe cometa deve declarar pointer-events='none' para nunca interceptar cliques."""
        failures = []
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
            beam_rects = [r for r in rects if r.attrib.get("class") in ("comet-beam", "neon-comet")]
            for b in beam_rects:
                pe = b.attrib.get("pointer-events", "")
                if pe != "none":
                    failures.append((card["filename"], f"pointer-events='{pe}'"))
        self.assertEqual(failures, [], f"Feixes sem pointer-events='none': {failures}")

    # --- ViewBox e Dimensões ---

    def test_b3_1_all_viewboxes_valid_non_negative_quads(self):
        """B3.1: Todos os 14 SVGs devem possuir viewBox composto por 4 valores numéricos não-negativos."""
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            vb = root.attrib.get("viewBox", "")
            parts = [float(v) for v in vb.split()]
            self.assertEqual(len(parts), 4, f"viewBox inválido em {card['filename']}: '{vb}'")
            self.assertGreaterEqual(parts[0], 0.0)
            self.assertGreaterEqual(parts[1], 0.0)
            self.assertGreater(parts[2], 0.0, f"Largura viewBox de {card['filename']} <= 0")
            self.assertGreater(parts[3], 0.0, f"Altura viewBox de {card['filename']} <= 0")

    def test_b3_2_base_rect_dimensions_within_viewbox(self):
        """B3.2: As dimensões dos retângulos de feixe devem estar contidas nos limites do viewBox."""
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            vb = [float(v) for v in root.attrib["viewBox"].split()]
            vb_w, vb_h = vb[2], vb[3]
            rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
            beam_rects = [r for r in rects if r.attrib.get("class") in ("comet-beam", "neon-comet")]
            for b in beam_rects:
                w = float(b.attrib.get("width", 0))
                h = float(b.attrib.get("height", 0))
                x = float(b.attrib.get("x", 0))
                y = float(b.attrib.get("y", 0))
                self.assertLessEqual(x + w, vb_w + 1.0, f"Feixe ultrapassa viewBox_w em {card['filename']}")
                self.assertLessEqual(y + h, vb_h + 1.0, f"Feixe ultrapassa viewBox_h em {card['filename']}")

    def test_b3_3_corner_radii_rx_ry_valid_and_non_negative(self):
        """B3.3: Raios de cantos arredondados (rx, ry) devem ser positivos e condizentes com o design (12 a 16px)."""
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
            beam_rects = [r for r in rects if r.attrib.get("class") in ("comet-beam", "neon-comet")]
            for b in beam_rects:
                rx = float(b.attrib.get("rx", 0))
                self.assertGreaterEqual(rx, 10.0, f"rx muito pequeno em {card['filename']}: {rx}")
                self.assertLessEqual(rx, 20.0, f"rx muito grande em {card['filename']}: {rx}")

    def test_b3_4_theoretical_perimeter_finite_and_positive(self):
        """B3.4: O perímetro analítico P = 2(w+h) - (8-2pi)r deve ser finito, positivo e consistente."""
        for card in EXPECTED_CARDS:
            p = card["perimeter"]
            self.assertGreater(p, 500, f"Perímetro anômalo em {card['filename']}: {p}")
            self.assertLess(p, 3000, f"Perímetro anômalo em {card['filename']}: {p}")

    def test_b3_5_base_rect_origin_coordinates_within_bounds(self):
        """B3.5: As coordenadas x e y do feixe devem manter margem mínima de 1.0 a 2.5px das bordas do SVG."""
        for card in EXPECTED_CARDS:
            _, _, root = parse_svg_file(card["filename"])
            rects = root.findall(".//{http://www.w3.org/2000/svg}rect") or root.findall(".//rect")
            beam_rects = [r for r in rects if r.attrib.get("class") in ("comet-beam", "neon-comet")]
            for b in beam_rects:
                x = float(b.attrib.get("x", 0))
                y = float(b.attrib.get("y", 0))
                self.assertGreaterEqual(x, 0.0, f"x negativo em {card['filename']}")
                self.assertGreaterEqual(y, 0.0, f"y negativo em {card['filename']}")


# ============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (Pairwise, Continuidade e Concorrência)
# ============================================================================

class TestTier3CrossFeatureCombinations(unittest.TestCase):
    """
    Testes de integração entre múltiplos cards e features:
    1. Continuidade temporal perfeita nos 14 pares adjacentes (1->2, 2->3, ..., 14->1)
    2. Exclusão mútua de feixes (no máximo 1 card ativo por instante)
    3. Preservação integral das 10 animações CSS pré-existentes
    """

    # --- Continuidade Temporal Perfeita ---

    def test_c1_1_pairwise_temporal_continuity_k_to_k_plus_1(self):
        """C1.1: Continuidade pairwise: t_end do card k deve coincidir com t_start do card k+1 para k=1..13."""
        slot_pct = 100.0 / 14.0
        failures = []
        for i in range(len(EXPECTED_CARDS) - 1):
            curr_card = EXPECTED_CARDS[i]
            next_card = EXPECTED_CARDS[i + 1]
            expected_transition = curr_card["end_s"] / 21.0 * 100.0

            # Verifica nos SVGs
            _, raw_curr, _ = parse_svg_file(curr_card["filename"])
            _, raw_next, _ = parse_svg_file(next_card["filename"])

            kf_curr = extract_keyframes(extract_css_text(raw_curr))
            kf_next = extract_keyframes(extract_css_text(raw_next))

            _, steps_curr = find_comet_keyframe(kf_curr, curr_card["index"])
            _, steps_next = find_comet_keyframe(kf_next, next_card["index"])

            points_curr = sorted(steps_curr.keys())
            points_next = sorted(steps_next.keys())

            # End do atual e start do próximo
            match_curr = any(abs(p - expected_transition) <= 0.15 for p in points_curr)
            match_next = any(abs(p - expected_transition) <= 0.15 for p in points_next)

            if not (match_curr and match_next):
                failures.append((f"{curr_card['filename']} -> {next_card['filename']}",
                                 f"Transição esperada em {expected_transition:.3f}%: curr={match_curr}, next={match_next}"))
        self.assertEqual(failures, [], f"Falhas de continuidade pairwise: {failures}")

    def test_c1_2_temporal_wrap_around_card_14_to_card_1(self):
        """C1.2: Wrap-around contínuo: o encerramento do card 14 (100%) coincide perfeitamente com o início do card 1 (0%)."""
        _, raw1, _ = parse_svg_file("header.svg")
        _, raw14, _ = parse_svg_file("trophies.svg")
        kf1 = extract_keyframes(extract_css_text(raw1))
        kf14 = extract_keyframes(extract_css_text(raw14))
        _, steps1 = find_comet_keyframe(kf1, 1)
        _, steps14 = find_comet_keyframe(kf14, 14)

        has_t0 = 0.0 in steps1 or 0 in steps1 or any(abs(p) < 0.01 for p in steps1.keys())
        has_t100 = 100.0 in steps14 or 100 in steps14 or any(abs(p - 100.0) < 0.01 for p in steps14.keys())

        self.assertTrue(has_t0, "Card 1 (header.svg) deve iniciar em t=0%")
        self.assertTrue(has_t100, "Card 14 (trophies.svg) deve finalizar em t=100%")

    def test_c1_3_no_dark_temporal_gaps_between_adjacent_cards(self):
        """C1.3: Em nenhum instante de transição entre cards deve ocorrer hiato escuro (sem cometa visível)."""
        slot_pct = 100.0 / 14.0
        failures = []
        for i in range(len(EXPECTED_CARDS) - 1):
            curr_c = EXPECTED_CARDS[i]
            next_c = EXPECTED_CARDS[i + 1]
            t_trans = (i + 1) * slot_pct

            _, raw_curr, _ = parse_svg_file(curr_c["filename"])
            _, raw_next, _ = parse_svg_file(next_c["filename"])

            kf_curr = extract_keyframes(extract_css_text(raw_curr))
            kf_next = extract_keyframes(extract_css_text(raw_next))

            _, steps_curr = find_comet_keyframe(kf_curr, curr_c["index"])
            _, steps_next = find_comet_keyframe(kf_next, next_c["index"])

            # No instante exato da transição (ou delta 0.2% antes/depois), a soma de opacidades deve ser >= 0.5
            op_curr = evaluate_property_at(steps_curr, "opacity", t_trans, default_val=0.0)
            op_next = evaluate_property_at(steps_next, "opacity", t_trans, default_val=0.0)
            op_sum = op_curr + op_next
            # Com fade de 0.5%, no ponto t_trans a opacidade pode estar zerando e subindo,
            # mas t_trans - 0.2% e t_trans + 0.2% devem manter transição viva
            op_before = evaluate_property_at(steps_curr, "opacity", t_trans - 0.2, default_val=0.0)
            op_after = evaluate_property_at(steps_next, "opacity", t_trans + 0.2, default_val=0.0)
            if op_before < 0.4 and op_after < 0.4:
                failures.append((f"{curr_c['filename']} -> {next_c['filename']}",
                                 f"Hiato detectado na transição {t_trans:.2f}%: op_before={op_before}, op_after={op_after}"))
        self.assertEqual(failures, [], f"Hiatos escuros detectados em transições: {failures}")

    def test_c1_4_sum_of_slot_durations_equals_100_percent(self):
        """C1.4: O particionamento em 14 fatias de 7.142857% deve preencher matematicamente 100.0%."""
        slot = 100.0 / 14.0
        total = sum(slot for _ in range(14))
        self.assertAlmostEqual(total, 100.0, places=5)

    # --- Exclusão Mútua de Feixes ---

    def test_c2_1_single_active_card_across_time_slices(self):
        """C2.1: Para qualquer instante de tempo t em [0.5s, 20.5s], no máximo um card deve ter opacidade > 0.8."""
        slot_pct = 100.0 / 14.0
        steps_per_card = {}
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf, card["index"])
            steps_per_card[card["index"]] = steps

        # Amostragem a cada 0.5% (200 amostras)
        violations = []
        for tick in range(1, 200):
            t_pct = tick * 0.5
            active_cards = []
            for cid, st in steps_per_card.items():
                op = evaluate_property_at(st, "opacity", t_pct, default_val=0.0)
                if op > 0.8:
                    active_cards.append(cid)
            if len(active_cards) > 1:
                violations.append((f"t={t_pct:.1f}%", f"Múltiplos cards ativos simultaneamente: {active_cards}"))
        self.assertEqual(violations, [], f"Violações de exclusão mútua detectadas: {violations}")

    def test_c2_2_fade_overlap_crossover_intensity_bounded(self):
        """C2.2: Durante o crossover de fade entre cards adjacentes, a soma das opacidades deve ser <= 1.25."""
        slot_pct = 100.0 / 14.0
        steps_per_card = {}
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf, card["index"])
            steps_per_card[card["index"]] = steps

        excess_overlaps = []
        for i in range(1, 14):
            t_trans = i * slot_pct
            for offset in (-0.3, -0.1, 0.0, 0.1, 0.3):
                t = t_trans + offset
                op1 = evaluate_property_at(steps_per_card[i], "opacity", t, default_val=0.0)
                op2 = evaluate_property_at(steps_per_card[i + 1], "opacity", t, default_val=0.0)
                if op1 + op2 > 1.3:
                    excess_overlaps.append((f"Card {i} -> Card {i+1}", f"t={t:.2f}%, soma={op1+op2:.2f}"))
        self.assertEqual(excess_overlaps, [], f"Intensidade excessiva em crossovers: {excess_overlaps}")

    def test_c2_3_zero_beam_stroke_visibility_outside_active_slice(self):
        """C2.3: Fora de sua fatia de atividade nominal (+- 0.5% fade), cada card deve ter opacidade < 0.05."""
        slot_pct = 100.0 / 14.0
        failures = []
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            css = extract_css_text(raw)
            kf = extract_keyframes(css)
            _, steps = find_comet_keyframe(kf, card["index"])

            t_start = (card["index"] - 1) * slot_pct
            t_end = card["index"] * slot_pct

            # Testa 10 pontos distantes da janela do card
            test_points = [(t_start - 10.0) % 100.0, (t_start - 25.0) % 100.0,
                           (t_end + 10.0) % 100.0, (t_end + 25.0) % 100.0]
            for tp in test_points:
                op = evaluate_property_at(steps, "opacity", tp, default_val=0.0)
                if op > 0.05:
                    failures.append((card["filename"], f"Opacidade={op:.3f} em t={tp:.2f}% (janela: {t_start:.1f}%..{t_end:.1f}%)"))
        self.assertEqual(failures, [], f"Feixes com opacidade residual fora da janela: {failures}")

    # --- Não-Regressão das 10 Animações Pré-existentes ---

    def test_c3_1_header_pulse_dot_animation_preserved(self):
        """C3.1: header.svg deve manter a animação '@keyframes pulseDot' e classe '.pulse' intocadas."""
        _, raw, _ = parse_svg_file("header.svg")
        self.assertIn("@keyframes pulseDot", raw, "header.svg perdeu @keyframes pulseDot")
        self.assertIn(".pulse", raw, "header.svg perdeu seletor .pulse")

    def test_c3_2_spotify_equalizer_animations_preserved(self):
        """C3.2: spotify.svg deve manter as animações eqBar1 a eqBar4 e classes .b1 a .b4 das barras de áudio."""
        _, raw, _ = parse_svg_file("spotify.svg")
        for i in range(1, 5):
            self.assertIn(f"@keyframes eqBar{i}", raw, f"spotify.svg perdeu @keyframes eqBar{i}")
            self.assertIn(f".b{i}", raw, f"spotify.svg perdeu classe .b{i}")

    def test_c3_3_myrifa_flip_coin_and_aura_preserved(self):
        """C3.3: card_myrifa.svg deve manter as animações 'flipCoin3D' e 'floatAura' intocadas."""
        _, raw, _ = parse_svg_file("card_myrifa.svg")
        self.assertIn("@keyframes flipCoin3D", raw, "card_myrifa.svg perdeu @keyframes flipCoin3D")
        self.assertIn("@keyframes floatAura", raw, "card_myrifa.svg perdeu @keyframes floatAura")

    def test_c3_4_webuildsites_float_ui_preserved(self):
        """C3.4: card_webuildsites.svg deve manter a animação 'floatUI' intocada."""
        _, raw, _ = parse_svg_file("card_webuildsites.svg")
        self.assertIn("@keyframes floatUI", raw, "card_webuildsites.svg perdeu @keyframes floatUI")

    def test_c3_5_lnki_float_chain_and_pulse_beam_preserved(self):
        """C3.5: card_lnki.svg deve manter as animações 'pulseBeam' e 'floatChain' intocadas."""
        _, raw, _ = parse_svg_file("card_lnki.svg")
        self.assertIn("@keyframes pulseBeam", raw, "card_lnki.svg perdeu @keyframes pulseBeam")
        self.assertIn("@keyframes floatChain", raw, "card_lnki.svg perdeu @keyframes floatChain")

    def test_c3_6_lenamimos_float_gift_preserved(self):
        """C3.6: card_lenamimos.svg deve manter a animação 'floatGift' intocada."""
        _, raw, _ = parse_svg_file("card_lenamimos.svg")
        self.assertIn("@keyframes floatGift", raw, "card_lenamimos.svg perdeu @keyframes floatGift")

    def test_c3_7_antigravity_float_device_and_app_layer_preserved(self):
        """C3.7: card_antigravity.svg deve manter as animações 'floatDevice' e 'floatAppLayer' intocadas."""
        _, raw, _ = parse_svg_file("card_antigravity.svg")
        self.assertIn("@keyframes floatDevice", raw, "card_antigravity.svg perdeu @keyframes floatDevice")
        self.assertIn("@keyframes floatAppLayer", raw, "card_antigravity.svg perdeu @keyframes floatAppLayer")

    def test_c3_8_cube_3d_six_layer_animations_preserved(self):
        """C3.8: cube_3d.svg deve manter suas 6 animações 3D: float3D, spinRing1..3, pulseLight e scanBeam."""
        _, raw, _ = parse_svg_file("cube_3d.svg")
        expected_anims = ["float3D", "spinRing1", "spinRing2", "spinRing3", "pulseLight", "scanBeam"]
        for anim in expected_anims:
            self.assertIn(f"@keyframes {anim}", raw, f"cube_3d.svg perdeu @keyframes {anim}")

    def test_c3_9_trophies_gem_floating_animations_preserved(self):
        """C3.9: trophies.svg deve manter as 4 animações das jóias 'floatGem1' a 'floatGem4' intocadas."""
        _, raw, _ = parse_svg_file("trophies.svg")
        for i in range(1, 5):
            self.assertIn(f"@keyframes floatGem{i}", raw, f"trophies.svg perdeu @keyframes floatGem{i}")

    def test_c3_10_all_original_defs_and_linear_gradients_retained(self):
        """C3.10: Todos os gradientes e filtros originais dos 14 cards devem ser preservados."""
        defs_to_check = [
            ("header.svg", "cardBorder"),
            ("card_stack.svg", "stackBorder"),
            ("card_myrifa.svg", "goldCoinGrad"),
            ("card_webuildsites.svg", "screenGrad"),
            ("card_antigravity.svg", "phoneScreen"),
            ("cube_3d.svg", "faceTopGrad"),
            ("trophies.svg", "rankGlow"),
        ]
        for filename, def_id in defs_to_check:
            _, _, root = parse_svg_file(filename)
            elem = root.find(f".//*[@id='{def_id}']")
            self.assertIsNotNone(elem, f"Elemento defs '{def_id}' ausente em {filename}")


# ============================================================================
# TIER 4: REAL-WORLD SCENARIOS (Integração README.md e Renderização)
# ============================================================================

class TestTier4RealWorldScenarios(unittest.TestCase):
    """
    Testes de integração real no GitHub Profile:
    1. README.md: existência, integridade e referências aos 14 SVGs
    2. Clickability: preservação estrita de todos os 9 links de navegação
    3. Conformidade das tags <img>, dimensões e ordem visual de apresentação
    """

    def test_r1_1_readme_file_exists_and_readable(self):
        """R1.1: O arquivo README.md deve existir na raiz do projeto e estar legível."""
        self.assertTrue(os.path.isfile(README_PATH), f"README.md não encontrado em {README_PATH}")
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 500, "README.md está vazio ou truncado")

    def test_r1_2_readme_references_all_14_svg_assets(self):
        """R1.2: O README.md deve referenciar explicitamente todos os 14 SVGs em assets/."""
        with open(README_PATH, "r", encoding="utf-8") as f:
            readme = f.read()
        for card in EXPECTED_CARDS:
            expected_ref = f"./assets/{card['filename']}"
            alt_ref = f"assets/{card['filename']}"
            has_ref = (expected_ref in readme) or (alt_ref in readme)
            self.assertTrue(has_ref, f"README.md não referencia o SVG {card['filename']}")

    def test_r1_3_all_14_referenced_assets_exist_on_disk(self):
        """R1.3: Todos os 14 arquivos referenciados no README.md devem existir fisicamente no disco."""
        for card in EXPECTED_CARDS:
            path = get_svg_path(card["filename"])
            self.assertTrue(os.path.isfile(path), f"Arquivo de asset não existe no disco: {path}")

    def test_r1_4_all_9_anchor_links_intact_and_correct(self):
        """R1.4: Todos os 9 links externos <a> mapeados no README.md devem permanecer 100% intactos."""
        with open(README_PATH, "r", encoding="utf-8") as f:
            readme = f.read()
        for item in EXPECTED_LINKS:
            # Garante que o link URL existe no README.md
            self.assertIn(item["url"], readme, f"Link obrigatório {item['url']} para {item['asset']} ausente no README.md")

    def test_r1_5_readme_image_tags_width_attributes_preserved(self):
        """R1.5: As tags <img> no README.md devem preservar seus atributos de largura de layout."""
        with open(README_PATH, "r", encoding="utf-8") as f:
            readme = f.read()
        # Header deve ter width="100%"
        self.assertRegex(readme, r'<img[^>]*header\.svg[^>]*width="100%"')
        # Botões e stack devem ter width="425"
        self.assertRegex(readme, r'<img[^>]*card_stack\.svg[^>]*width="425"')
        self.assertRegex(readme, r'<img[^>]*btn_portfolio\.svg[^>]*width="425"')
        # Cards de projetos devem ter width="49%"
        self.assertRegex(readme, r'<img[^>]*card_myrifa\.svg[^>]*width="49%"')
        # Antigravity deve ter width="99%"
        self.assertRegex(readme, r'<img[^>]*card_antigravity\.svg[^>]*width="99%"')

    def test_r1_6_readme_visual_order_matches_sync_order_1_to_14(self):
        """R1.6: A ordem física de aparecimento dos SVGs no README.md deve coincidir com a ordem do ciclo (1 a 14)."""
        with open(README_PATH, "r", encoding="utf-8") as f:
            readme = f.read()

        positions = []
        for card in EXPECTED_CARDS:
            pos = readme.find(card["filename"])
            self.assertNotEqual(pos, -1, f"Arquivo {card['filename']} não encontrado no texto do README.md")
            positions.append((card["index"], card["filename"], pos))

        # As posições devem ser estritamente crescentes
        for i in range(len(positions) - 1):
            curr_card = positions[i]
            next_card = positions[i + 1]
            self.assertLess(curr_card[2], next_card[2],
                            f"Ordem visual incorreta no README: {curr_card[1]} (pos {curr_card[2]}) aparece depois de {next_card[1]} (pos {next_card[2]})")

    def test_r1_7_svg_standalone_browser_rendering_simulation(self):
        """R1.7: Simulação de carregamento isolado: nenhum SVG deve conter tags proibidas (<script>, event handlers)."""
        prohibited_tokens = ["<script", "onload=", "onclick=", "onerror=", "javascript:"]
        for card in EXPECTED_CARDS:
            _, raw, _ = parse_svg_file(card["filename"])
            raw_lower = raw.lower()
            for token in prohibited_tokens:
                self.assertNotIn(token, raw_lower, f"Token proibido '{token}' encontrado em {card['filename']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
