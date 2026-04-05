#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║              💀  S P L O I T U S . P Y  💀                     ║
║         Exploit & Hacktool Search Engine CLI Tool               ║
║     Powered by: https://sploitus.com/  (Unofficial Client)      ║
╚══════════════════════════════════════════════════════════════════╝

EXAMPLES:
  Search both exploits AND tools (default):
    sploitus.py -q "apache"
    sploitus.py -q "log4j" -l 15 --stats

  Exploits only:
    sploitus.py -q "CVE-2024-1234" -t exploits -s score -l 10
    sploitus.py -q "apache" -t exploits -s date -v

  Tools only:
    sploitus.py -q "nmap" -t tools -l 10
    sploitus.py -q "scanner" -t tools -s default

  Output formats:
    sploitus.py -q "rce" -t exploits -o json
    sploitus.py -q "rce" -t exploits -o minimal
    sploitus.py -q "rce" -t exploits -o json --save results.json

  Lookup by Sploitus ID:
    sploitus.py --id "EDB-ID:51582"
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from urllib.parse import quote as url_quote

# ── Constants ─────────────────────────────────────────────────────────────────

API_URL     = "https://sploitus.com/search"
EXPLOIT_URL = "https://sploitus.com/exploit?id={}"
PAGE_SIZE   = 25
MAX_RESULTS = 500

# ── Colors ────────────────────────────────────────────────────────────────────

class C:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"

def col(color, text):
    if not sys.stdout.isatty():
        return str(text)
    return f"{color}{text}{C.RESET}"

# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = r"""
  ███████╗██████╗ ██╗      ██████╗ ██╗████████╗██╗   ██╗███████╗
  ██╔════╝██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝██║   ██║██╔════╝
  ███████╗██████╔╝██║     ██║   ██║██║   ██║   ██║   ██║███████╗
  ╚════██║██╔═══╝ ██║     ██║   ██║██║   ██║   ██║   ██║╚════██║
  ███████║██║     ███████╗╚██████╔╝██║   ██║   ╚██████╔╝███████║
  ╚══════╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝   ╚═╝    ╚═════╝ ╚══════╝"""

def print_banner():
    print(col(C.RED, BANNER))
    print(col(C.DIM, "  💀 Exploit & Hacktool Search Engine  |  https://sploitus.com/"))
    print(col(C.DIM, "  " + "─" * 64))
    print()

# ── HTTP via curl (bypasses Cloudflare JS challenge) ──────────────────────────

def _check_curl():
    if not shutil.which("curl"):
        print(col(C.RED, "[!] 'curl' is not installed. Install it with: sudo apt install curl"))
        sys.exit(1)

def _api_search(query: str, qtype: str, sort: str,
                offset: int, title_only: bool, timeout: int) -> dict:
    """
    Calls sploitus.com/search via curl subprocess.
    curl sends proper TLS fingerprints + handles gzip/br (--compressed)
    which bypasses Cloudflare's bot challenge that blocks pure Python requests.

    The Referer is set dynamically to match the section the user is browsing:
      https://sploitus.com/?query=<q>#exploits  or  #tools
    This is the key header Cloudflare validates for same-origin XHR.
    """
    section = "exploits" if qtype == "exploits" else "tools"
    referer = f"https://sploitus.com/?query={url_quote(query)}#{section}"
    payload = json.dumps({
        "type":   qtype,
        "query":  query,
        "sort":   sort,
        "title":  title_only,
        "offset": offset,
    })

    cmd = [
        "curl", "-s", "--compressed",
        "-X", "POST", API_URL,
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json, text/plain, */*",
        "-H", "Accept-Language: en-US,en;q=0.9",
        "-H", f"Origin: https://sploitus.com",
        "-H", f"Referer: {referer}",
        "-H", "Sec-Fetch-Dest: empty",
        "-H", "Sec-Fetch-Mode: cors",
        "-H", "Sec-Fetch-Site: same-origin",
        "-H", "Sec-CH-UA: \"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\"",
        "-H", "Sec-CH-UA-Mobile: ?0",
        "-H", "Sec-CH-UA-Platform: \"Linux\"",
        "-H", ("User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
        "-H", "DNT: 1",
        "--max-time", str(timeout),
        "-d", payload,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        if result.returncode != 0:
            _die(f"[!] curl failed (exit {result.returncode}): {result.stderr.strip()}")
        if not result.stdout.strip():
            _die("[!] Empty response from sploitus.com")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # Cloudflare HTML challenge page
            if "Just a moment" in result.stdout or "<!DOCTYPE" in result.stdout[:50]:
                _die("[!] Cloudflare is blocking the request.\n"
                     "    Try again in a few seconds, or change your network/VPN.")
            _die(f"[!] Invalid JSON response:\n{result.stdout[:300]}")
    except subprocess.TimeoutExpired:
        _die(f"[!] Request timed out after {timeout}s.")
    return {}


def _die(msg: str):
    print(col(C.RED, msg))
    sys.exit(1)

# ── Pagination ────────────────────────────────────────────────────────────────

def fetch_pages(query: str, qtype: str, sort: str,
                title_only: bool, max_results: int, timeout: int):
    collected = []
    offset    = 0
    total     = 0

    while len(collected) < max_results and offset <= MAX_RESULTS:
        data  = _api_search(query, qtype, sort, offset, title_only, timeout)
        batch = data.get("exploits", [])
        total = int(data.get("exploits_total", 0))

        if not batch:
            break
        collected.extend(batch)
        offset += PAGE_SIZE
        if offset >= total:
            break

    return collected[:max_results], total

# ── Display helpers ───────────────────────────────────────────────────────────

SOURCE_COLOR = {
    "exploitdb":     C.GREEN,
    "packetstorm":   C.YELLOW,
    "metasploit":    C.CYAN,
    "vulhub":        C.MAGENTA,
    "kitploit":      C.BLUE,
    "exploitpack":   C.RED,
    "githubexploit": C.WHITE,
}

def _src_col(src: str) -> str:
    for k, v in SOURCE_COLOR.items():
        if k in src.lower():
            return v
    return C.WHITE

def _score_col(score) -> str:
    try:
        s = float(score)
        if s >= 7.5: return C.RED
        if s >= 5.0: return C.YELLOW
        return C.GREEN
    except (TypeError, ValueError):
        return C.WHITE

def _trunc(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n - 3] + "..."

def _fmt_date(d: str) -> str:
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return d or "N/A"

def _sep(ch="─", w=80):
    print(col(C.DIM, ch * w))

def _dot():
    print(col(C.DIM, "·" * 80))

# ── Print: Exploits ───────────────────────────────────────────────────────────

def print_exploits(results: list, total: int, query: str, verbose: bool = False):
    site_link = f"https://sploitus.com/?query={url_quote(query)}#exploits"
    print(col(C.BOLD, "\n  🔍 Query  : ") + col(C.CYAN,   f'"{query}"'))
    print(col(C.BOLD, "  💀 Section: ") + col(C.RED,    "Exploits") +
          col(C.DIM,  f"  [ {site_link} ]"))
    print(col(C.BOLD, "  📈 Total  : ") + col(C.YELLOW, str(total)) +
          col(C.DIM,  f"  (showing {len(results)})"))
    print()
    _sep()

    for idx, item in enumerate(results, 1):
        title   = item.get("title", "N/A").replace("&quot;", '"')
        score   = item.get("score", 0)
        href    = item.get("href", "")
        etype   = item.get("type", "unknown")
        pub     = _fmt_date(item.get("published", ""))
        eid     = item.get("id", "")
        lang    = item.get("language", "")
        spl_url = EXPLOIT_URL.format(eid) if eid else ""

        num_s   = col(C.DIM,            f"[{idx:>3}]")
        score_s = col(_score_col(score), f"▶ {float(score or 0):.1f}")
        type_s  = col(_src_col(etype),  f"[{etype.upper()}]")
        lang_s  = col(C.DIM, f"({lang})") if lang else ""

        print(f"  {num_s} {score_s}  {col(C.BOLD, _trunc(title, 60))}  {type_s} {lang_s}")
        print(f"         {col(C.DIM, f'📅 {pub}  🆔 {eid}')}")

        if href:
            print(f"         {col(C.BLUE,  '🔗 Source  :')} {col(C.CYAN, href)}")
        if spl_url and spl_url != href:
            print(f"         {col(C.BLUE,  '💀 Sploitus :')} {col(C.DIM, spl_url)}")

        if verbose and item.get("source"):
            lines = [ln for ln in item["source"].split("\n")
                     if not ln.strip().startswith("## https://sploitus.com")]
            print()
            print(col(C.DIM, "    ┌─ Source Preview " + "─" * 42))
            for ln in lines[:14]:
                print(col(C.DIM, f"    │  {ln}"))
            if len(lines) > 14:
                print(col(C.DIM, f"    │  ... ({len(lines)} total lines)"))
            print(col(C.DIM, "    └" + "─" * 50))

        _dot()

# ── Print: Tools ──────────────────────────────────────────────────────────────

def print_tools(results: list, total: int, query: str):
    site_link = f"https://sploitus.com/?query={url_quote(query)}#tools"
    print(col(C.BOLD, "\n  🔍 Query  : ") + col(C.CYAN,    f'"{query}"'))
    print(col(C.BOLD, "  🛠  Section: ") + col(C.MAGENTA, "Tools") +
          col(C.DIM,  f"  [ {site_link} ]"))
    print(col(C.BOLD, "  📈 Total  : ") + col(C.YELLOW,  str(total)) +
          col(C.DIM,  f"  (showing {len(results)})"))
    print()
    _sep()

    for idx, item in enumerate(results, 1):
        title    = item.get("title", "N/A").replace("&quot;", '"')
        etype    = item.get("type", "unknown")
        href     = item.get("href", "")
        download = item.get("download", "")
        eid      = item.get("id", "")

        type_s = col(_src_col(etype), f"[{etype.upper()}]")
        num_s  = col(C.DIM,           f"[{idx:>3}]")

        print(f"  {num_s}  {col(C.BOLD, _trunc(title, 65))}  {type_s}")
        if eid:
            print(f"          {col(C.DIM, f'🆔 {eid}')}")
        if href:
            print(f"          {col(C.BLUE,  '🔗 Info     :')} {col(C.CYAN, href)}")
        if download:
            print(f"          {col(C.GREEN, '📥 Download :')} {col(C.CYAN, download)}")
        _dot()

# ── Both sections ─────────────────────────────────────────────────────────────

def cmd_both(query: str, sort: str, limit: int, title_only: bool,
             timeout: int, output: str, verbose: bool, stats: bool, save: str):
    """
    Queries both:
      https://sploitus.com/?query=<query>#exploits
      https://sploitus.com/?query=<query>#tools
    """
    if output == "table":
        print(col(C.BOLD + C.CYAN, f'\n  🔍 Dual Search: "{query}"'))
        print(col(C.DIM, "  ─" * 40))
        print(col(C.RED + C.BOLD, "\n  ╔══════════════  💀 EXPLOITS section  ══════════════╗"))

    exp_data    = _api_search(query, "exploits", sort, 0, title_only, timeout)
    exp_results = exp_data.get("exploits", [])[:limit]
    exp_total   = int(exp_data.get("exploits_total", 0))

    if output == "table":
        print(col(C.MAGENTA + C.BOLD, "  ╔══════════════  🛠  TOOLS section  ═══════════════╗"))

    tool_data    = _api_search(query, "tools", sort, 0, title_only, timeout)
    tool_results = tool_data.get("exploits", [])[:limit]
    tool_total   = int(tool_data.get("exploits_total", 0))

    if output == "json":
        payload = {
            "query": query,
            "exploits": {"total": exp_total,  "count": len(exp_results),  "results": exp_results},
            "tools":    {"total": tool_total, "count": len(tool_results), "results": tool_results},
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    elif output == "minimal":
        print("# --- EXPLOITS ---")
        for r in exp_results:
            eid = r.get("id", "")
            url = EXPLOIT_URL.format(eid) if eid else r.get("href", "")
            scr = r.get("score", "")
            print(f"{url}{'  ['+str(scr)+']' if scr else ''}  # {r.get('title','').replace('&quot;','\"')}")
        print("# --- TOOLS ---")
        for r in tool_results:
            url = r.get("download", "") or r.get("href", "")
            print(f"{url}  # {r.get('title','').replace('&quot;','\"')}")

    else:
        if exp_results:
            print_exploits(exp_results, exp_total, query, verbose=verbose)
        else:
            print(col(C.YELLOW, "\n  [!] No exploits found."))

        if tool_results:
            print_tools(tool_results, tool_total, query)
        else:
            print(col(C.YELLOW, "\n  [!] No tools found."))

        if stats:
            _print_stats(exp_results,  "Exploits")
            _print_stats(tool_results, "Tools")

    if save:
        payload = {
            "query":    query,
            "saved_at": datetime.now().isoformat(),
            "exploits": {"total": exp_total,  "results": exp_results},
            "tools":    {"total": tool_total, "results": tool_results},
        }
        with open(save, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(col(C.GREEN, f"\n  [+] Saved → {save}"))

# ── JSON / Minimal output ─────────────────────────────────────────────────────

def print_json(results: list, total: int, query: str, qtype: str):
    out = {"query": query, "type": qtype, "total": total,
           "count": len(results), "results": results}
    print(json.dumps(out, indent=2, ensure_ascii=False))

def print_minimal(results: list):
    for r in results:
        eid   = r.get("id", "")
        href  = r.get("href", "") or r.get("download", "")
        title = r.get("title", "").replace("&quot;", '"')
        score = r.get("score", "")
        url   = EXPLOIT_URL.format(eid) if eid else href
        score_s = f" [{score}]" if score else ""
        print(f"{url}{score_s}  # {title}")

# ── Stats ─────────────────────────────────────────────────────────────────────

def _print_stats(results: list, label: str = "Results"):
    if not results:
        return
    types  = {}
    langs  = {}
    scores = []
    dates  = []

    for r in results:
        t = r.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
        lg = r.get("language", "")
        if lg:
            langs[lg] = langs.get(lg, 0) + 1
        try:
            scores.append(float(r.get("score", 0)))
        except Exception:
            pass
        d = r.get("published", "")
        if d:
            dates.append(d)

    _sep()
    print(col(C.BOLD, f"\n  📈  Stats — {label}\n"))

    print(col(C.YELLOW, "  📂 By Source:"))
    for t, cnt in sorted(types.items(), key=lambda x: -x[1]):
        bar = "█" * min(cnt, 30)
        print(f"     {col(_src_col(t), f'{t:<22}')}{col(C.CYAN, bar)} {cnt}")

    if langs:
        print(col(C.YELLOW, "\n  💻 By Language:"))
        for lg, cnt in sorted(langs.items(), key=lambda x: -x[1])[:8]:
            print(f"     {col(C.CYAN, f'{lg:<22}')} {cnt}")

    if scores:
        avg_s = sum(scores) / len(scores)
        max_s = max(scores)
        high  = sum(1 for s in scores if s >= 7.5)
        print(col(C.YELLOW, "\n  ⚡ Score Stats:"))
        print(f"     Average   : {col(C.YELLOW, f'{avg_s:.2f}')}")
        print(f"     Max       : {col(C.RED,    f'{max_s:.2f}')}")
        print(f"     High ≥7.5 : {col(C.RED,    str(high))}")

    if dates:
        dates.sort()
        print(col(C.YELLOW, "\n  📅 Date Range:"))
        print(f"     Oldest : {col(C.DIM,   _fmt_date(dates[0]))}")
        print(f"     Newest : {col(C.GREEN, _fmt_date(dates[-1]))}")
    print()

# ── Lookup by ID ──────────────────────────────────────────────────────────────

def lookup_id(exploit_id: str, timeout: int):
    url = EXPLOIT_URL.format(exploit_id)
    print(col(C.CYAN, f"\n[*] Sploitus URL: {url}"))
    data    = _api_search(exploit_id, "exploits", "default", 0, False, timeout)
    results = data.get("exploits", [])
    total   = int(data.get("exploits_total", 0))
    if results:
        print_exploits(results[:1], total, exploit_id, verbose=True)
    else:
        print(col(C.YELLOW, f"[!] No results for ID: {exploit_id}"))
        print(col(C.DIM,    f"    Visit: {url}"))

# ── Argument Parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sploitus.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )

    p.add_argument("-q", "--query", type=str,
                   help="Search keyword or CVE ID")
    p.add_argument("--id", type=str, metavar="ID",
                   help="Look up exploit by Sploitus ID (e.g. EDB-ID:51582)")

    p.add_argument("-t", "--type", type=str, default="both",
                   choices=["exploits", "tools", "both"],
                   help="Section: exploits | tools | both (default: both)")
    p.add_argument("-s", "--sort", type=str, default="default",
                   choices=["default", "date", "score"],
                   help="Sort: default (relevance) | date | score")
    p.add_argument("--title", action="store_true",
                   help="Search in titles only")

    p.add_argument("-l", "--limit", type=int, default=10, metavar="N",
                   help="Results per section to display (default: 10)")
    p.add_argument("--offset", type=int, default=0,
                   help="Pagination offset (default: 0)")
    p.add_argument("--all", action="store_true",
                   help="Fetch ALL pages (up to 500 results)")

    p.add_argument("-o", "--output", type=str, default="table",
                   choices=["table", "json", "minimal"],
                   help="Output format: table | json | minimal")
    p.add_argument("--save", type=str, metavar="FILE",
                   help="Save JSON results to file")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Show source code preview (exploits)")
    p.add_argument("--stats", action="store_true",
                   help="Show stats summary")
    p.add_argument("--no-banner", action="store_true",
                   help="Suppress ASCII banner")
    p.add_argument("--timeout", type=int, default=20, metavar="SECS",
                   help="HTTP timeout in seconds (default: 20)")

    return p

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    _check_curl()
    parser = build_parser()
    args   = parser.parse_args()

    if not args.no_banner and args.output == "table":
        print_banner()

    if args.id:
        lookup_id(args.id, args.timeout)
        return

    if not args.query:
        parser.print_help()
        print(col(C.RED, "\n[!] --query is required (or use --id for ID lookup)."))
        sys.exit(1)

    query = args.query.strip()
    limit = min(max(1, args.limit), MAX_RESULTS)

    if args.type == "both":
        cmd_both(
            query=query, sort=args.sort, limit=limit,
            title_only=args.title, timeout=args.timeout,
            output=args.output, verbose=args.verbose,
            stats=args.stats, save=args.save or "",
        )
        return

    if args.output == "table":
        print(col(C.CYAN, "[*] Searching: ") + col(C.BOLD, f'"{query}"') +
              col(C.DIM,  f"  type={args.type}  sort={args.sort}  limit={limit}"))

    if args.all or limit > PAGE_SIZE:
        results, total = fetch_pages(query, args.type, args.sort,
                                     args.title, limit, args.timeout)
    else:
        data    = _api_search(query, args.type, args.sort,
                              args.offset, args.title, args.timeout)
        results = data.get("exploits", [])[:limit]
        total   = int(data.get("exploits_total", 0))

    if not results:
        print(col(C.YELLOW, f"[!] No results found for: {query}"))
        sys.exit(0)

    if args.output == "json":
        print_json(results, total, query, args.type)
    elif args.output == "minimal":
        print_minimal(results)
    else:
        if args.type == "tools":
            print_tools(results, total, query)
        else:
            print_exploits(results, total, query, verbose=args.verbose)
        if args.stats:
            _print_stats(results, args.type.capitalize())

    if args.save:
        out = {"query": query, "type": args.type, "total": total,
               "saved_at": datetime.now().isoformat(), "results": results}
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(col(C.GREEN, f"\n[+] Saved → {args.save}"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(col(C.YELLOW, "\n\n[!] Interrupted."))
        sys.exit(0)
