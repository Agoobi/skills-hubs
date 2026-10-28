#!/usr/bin/env python3
"""Edit and deploy aiagentvn.com landing pages (theme repo Agoobi/aiagentvn-theme).

    python landing.py find <url-or-slug>        which files make up a landing page
    python landing.py preview <key>             local preview: the live page with your local edits swapped in
    python landing.py plan [--base SHA]         what GitHub main would change on the live site (read-only)
    python landing.py deploy [--base SHA]       back up, upload, purge cache, verify
    python landing.py rollback <stamp>          put back the files a deploy replaced

Run it from inside a clone of the theme repo, or pass --repo PATH.
deploy only ships a clean checkout of the remote main branch, never local edits.

Hosting credentials come from the environment (ask the site owner; never commit, paste or log them):
    ONEPANEL_MCP_URL     the OnePanel MCP endpoint
    ONEPANEL_MCP_TOKEN   its bearer token
"""
import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

DOMAIN = "aiagentvn.com"
REMOTE_THEME = "public_html/wp-content/themes/aiagentvn-theme"
THEME_URL = "https://%s/wp-content/themes/aiagentvn-theme/" % DOMAIN
# Kept outside public_html: backups of .php files would otherwise be served as plain source.
BACKUPS = "aiavn-backups"
MARKER = BACKUPS + "/deployed-commit"
# never shipped: dev tooling, legacy landing sources, tests, prebuilt apps
SKIP = ("tools/", "scripts/", "tests/", "assets/apps/", ".git", "README.md")
PACK_BYTES = 90_000  # base64 per pack; the hosting API handles ~120 KB of text per call
PAUSE = 1.1          # seconds between API calls; bursts get HTTP 429


# ---------------------------------------------------------------- hosting API
class OnePanel:
    def __init__(self):
        self.url = os.environ.get("ONEPANEL_MCP_URL", "")
        self.token = os.environ.get("ONEPANEL_MCP_TOKEN", "")
        if not (self.url and self.token):
            sys.exit("Set ONEPANEL_MCP_URL and ONEPANEL_MCP_TOKEN (ask the site owner).")
        self.sid = None

    def _post(self, body):
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "Authorization": "Bearer " + self.token}
        if self.sid:
            headers["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers=headers)
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=180) as res:
                    raw = res.read().decode("utf-8", "replace")
                    self.sid = res.headers.get("Mcp-Session-Id") or self.sid
                break
            except urllib.error.HTTPError as err:
                if err.code != 429 or attempt == 4:
                    raise
                time.sleep(20 * (attempt + 1))
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                if attempt == 4:  # the host drops connections now and then; every call here is safe to repeat
                    raise
                time.sleep(20 * (attempt + 1))
        if raw.lstrip().startswith(("event:", "data:")):
            raw = [line[5:].strip() for line in raw.splitlines() if line.startswith("data:")][-1]
        return json.loads(raw) if raw.strip() else {}

    def call(self, tool, **args):
        if not self.sid:
            self._post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "aiavn-landing", "version": "1"}}})
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        time.sleep(PAUSE)
        res = self._post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool, "arguments": args}})
        result = res.get("result", {})
        text = "\n".join(c.get("text", "") for c in result.get("content", []))
        if res.get("error") or result.get("isError"):
            raise RuntimeError("%s failed: %s" % (tool, text or res.get("error")))
        return text

    def read(self, path):
        """Text content of a hosting file, or None when it does not exist."""
        try:
            raw = self.call("read_file", path=path)
        except RuntimeError:
            return None
        try:
            raw = json.loads(raw).get("content", raw)
        except (ValueError, AttributeError):
            pass
        return raw.replace("\r\n", "\n")

    def dirs(self, path):
        try:
            data = json.loads(self.call("list_files", path=path))
        except (RuntimeError, ValueError):
            return None
        return {d["basename"] for d in data.get("directories", [])}


# ---------------------------------------------------------------- repo helpers
def git(repo, *args, check=True):
    out = subprocess.run(["git", *args], cwd=repo, capture_output=True)
    if check and out.returncode:
        sys.exit("git %s failed: %s" % (" ".join(args), out.stderr.decode(errors="replace").strip()))
    return out.stdout


def find_repo(path):
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path, capture_output=True, text=True).stdout.strip()
    if not top or not os.path.isfile(os.path.join(top, "inc", "site", "landing.php")):
        sys.exit("Not inside the aiagentvn-theme repo; cd into your clone or pass --repo.")
    return top


def main_remote(repo):
    for line in git(repo, "remote", "-v").decode().splitlines():
        name, url = line.split()[:2]
        if "Agoobi/aiagentvn-theme" in url:
            return name
    sys.exit("No git remote points at Agoobi/aiagentvn-theme.")


def registry(repo):
    """landing key -> slug, from the generated registry."""
    text = open(os.path.join(repo, "inc", "site", "landing.php"), encoding="utf-8").read()
    return dict(re.findall(r"^    '([\w-]+)' => \[\s*\n\s*'slug' => '([^']*)'", text, re.M))


def is_text(data):
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def live_bytes(rel):
    url = THEME_URL + rel + "?nocache=" + secrets.token_hex(4)
    try:
        with urllib.request.urlopen(url, timeout=60) as res:
            return res.read()
    except urllib.error.HTTPError:
        return None


# ---------------------------------------------------------------- commands
def cmd_find(repo, target):
    slug = re.sub(r"^https?://[^/]+", "", target).strip("/").split("?")[0].split("#")[0]
    reg = registry(repo)
    hits = [k for k, s in reg.items() if s == slug or k == slug]
    if not hits:
        sys.exit("No landing page with slug '%s'. The homepage, blog and hub pages are not landing pages." % slug)
    for key in hits:
        print("page key: %s   url: https://%s/%s/" % (key, DOMAIN, reg[key]))
        for rel in ["pages/landing/%s.html" % key] + ["assets/landing/%s%s" % (key, ext) for ext in (".css", ".js", ".tw.css", ".app.js")]:
            if os.path.isfile(os.path.join(repo, rel)):
                print("  ", rel)


def cmd_preview(repo, key):
    reg = registry(repo)
    if key not in reg:
        sys.exit("Unknown page key '%s'; run: landing.py find <url>" % key)
    with urllib.request.urlopen("https://%s/%s/?preview=%s" % (DOMAIN, reg[key], secrets.token_hex(3)), timeout=90) as res:
        page = res.read().decode("utf-8")
    body = open(os.path.join(repo, "pages", "landing", key + ".html"), encoding="utf-8").read()
    body = body.replace("{{static}}", THEME_URL + "assets/root-static/")
    m = re.search(r'(<main\b[^>]*class="pg pg-%s\b[^"]*"[^>]*>)(.*?)(</main>)' % re.escape(key), page, re.S)
    if not m:
        sys.exit("Could not find the page body on the live page.")
    page = page[:m.start(2)] + "\n" + body + "\n" + page[m.end(2):]
    for ext in (".css", ".js", ".tw.css", ".app.js"):
        local = os.path.join(repo, "assets", "landing", key + ext)
        if os.path.isfile(local):
            page = re.sub(r"https?://%s/wp-content/themes/aiagentvn-theme/assets/landing/%s%s\?v=\d+" % (
                re.escape(DOMAIN), re.escape(key), re.escape(ext)), "file:///" + local.replace("\\", "/"), page)
    out = os.path.join(tempfile.gettempdir(), "aiavn-preview-%s.html" % key)
    open(out, "w", encoding="utf-8").write(page)
    print(out)
    print("Open it in a browser (desktop and phone width). Header/footer are the live ones; only this page body, CSS and JS are local.")


def changed_files(repo, base):
    out = git(repo, "diff", "--name-status", "--no-renames", base, "HEAD").decode().splitlines()
    files, deleted = [], []
    for line in out:
        status, rel = line.split("\t", 1)
        if rel.startswith(SKIP):
            continue
        (deleted if status == "D" else files).append(rel)
    return files, deleted


def prepare(repo, op, base):
    remote = main_remote(repo)
    git(repo, "fetch", "--quiet", remote)
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    main = git(repo, "rev-parse", remote + "/main").decode().strip()
    if head != main:
        sys.exit("HEAD is not %s/main. Deploy from a clean checkout of main:\n  git switch --detach %s/main" % (remote, remote))
    if git(repo, "status", "--porcelain").strip():
        sys.exit("Working tree has local changes. Deploy ships GitHub main only; commit them through a PR first.")
    if not base:
        base = (op.read(MARKER) or "").strip()
        if not base:
            sys.exit("The hosting has no ~/%s marker yet. Pass --base <commit that is live now>." % MARKER)
    if git(repo, "cat-file", "-t", base, check=False).strip() != b"commit":
        sys.exit("Base %s is not a commit in this repo." % base)
    files, deleted = changed_files(repo, base)
    plan = []
    for rel in files:
        data = git(repo, "show", "HEAD:" + rel)
        if is_text(data):
            live = op.read(REMOTE_THEME + "/" + rel)
            new = data.decode("utf-8").replace("\r\n", "\n")
            if live != new:
                plan.append((rel, "text", live, new))
        else:
            if live_bytes(rel) != data:
                plan.append((rel, "binary", None, data))
    return head, base, plan, deleted


def show_plan(head, base, plan, deleted):
    print("live base %s -> main %s" % (base[:7], head[:7]))
    if not plan:
        print("Nothing to deploy: the live files already match main.")
    for rel, kind, live, _ in plan:
        print("  %-8s %-6s %s" % ("new" if live is None and kind == "text" else "update", kind, rel))
    for rel in deleted:
        print("  ! %s was deleted in main; it stays on the server (ask the site owner)." % rel)


def ensure_dirs(op, rels, known):
    for rel_dir in sorted({os.path.dirname(r) for r in rels} - {""}, key=lambda d: d.count("/")):
        parent, name = os.path.split(rel_dir)
        remote_parent = REMOTE_THEME + ("/" + parent if parent else "")
        if remote_parent not in known:
            known[remote_parent] = op.dirs(remote_parent) or set()
        if name not in known[remote_parent]:
            op.call("create_directory", path=remote_parent, name=name)
            known[remote_parent].add(name)
            known[REMOTE_THEME + "/" + rel_dir] = set()


def install_binaries(op, items):
    """The text-only file API corrupts binaries, so they travel as base64 packs that a one-shot PHP installer unpacks."""
    packs, current, size = [], {}, 0
    for rel, data in items:
        entry = {"b64": base64.b64encode(data).decode(), "sha256": hashlib.sha256(data).hexdigest()}
        if current and size + len(entry["b64"]) > PACK_BYTES:
            packs.append(current)
            current, size = {}, 0
        current[rel] = entry
        size += len(entry["b64"])
    packs.append(current)
    op.call("create_directory", path="", name="aiavn-deploy")
    names = []
    for i, pack in enumerate(packs):
        names.append("pack-%02d.json" % i)
        op.call("write_file", path="aiavn-deploy/" + names[-1], content=json.dumps(pack))
    token, script = secrets.token_hex(24), "aiavn-install-%s.php" % secrets.token_hex(6)
    php = """<?php
// One-shot installer written by landing.py: unpacks base64 file packs, then removes itself.
if (!hash_equals('%s', (string) ($_GET['t'] ?? ''))) { http_response_code(404); exit; }
$home = dirname(__DIR__);
$done = 0; $bad = [];
foreach (%s as $pack) {
    $path = $home . '/aiavn-deploy/' . $pack;
    $files = json_decode((string) file_get_contents($path), true) ?: [];
    foreach ($files as $rel => $meta) {
        $bytes = base64_decode($meta['b64'], true);
        $dest = $home . '/%s/' . $rel;
        if ($bytes === false || hash('sha256', $bytes) !== $meta['sha256'] || strpos($rel, '..') !== false) { $bad[] = $rel; continue; }
        if (!is_dir(dirname($dest))) { mkdir(dirname($dest), 0755, true); }
        if (file_put_contents($dest, $bytes) === strlen($bytes)) { $done++; } else { $bad[] = $rel; }
    }
    unlink($path);
}
@rmdir($home . '/aiavn-deploy');
unlink(__FILE__);
header('Content-Type: application/json');
echo json_encode(['written' => $done, 'failed' => $bad]);
""" % (token, "['" + "', '".join(names) + "']", REMOTE_THEME)
    op.call("write_file", path="public_html/" + script, content=php)
    with urllib.request.urlopen("https://%s/%s?t=%s" % (DOMAIN, script, token), timeout=120) as res:
        report = json.loads(res.read().decode())
    if report.get("failed"):
        sys.exit("Binary install failed for %s" % report["failed"])
    return report.get("written")


def cmd_deploy(repo, base, apply):
    op = OnePanel()
    head, base, plan, deleted = prepare(repo, op, base)
    show_plan(head, base, plan, deleted)
    if not apply:
        if plan:
            print("\nPlan only. Run with deploy to apply it.")
        return
    if not plan:  # live already matches main: just record that, so later runs need no --base
        if BACKUPS not in (op.dirs("") or set()):
            op.call("create_directory", path="", name=BACKUPS)
        op.call("write_file", path=MARKER, content=head + "\n")
        print("Recorded %s as the live commit." % head[:7])
        return
    stamp = time.strftime("%Y%m%d-%H%M%S")
    manifest = {"stamp": stamp, "from": base, "to": head, "backups": [], "created": []}
    ensure_dirs(op, [rel for rel, *_ in plan], {})
    # 1. back up every text file that exists live, before anything is written (~/aiavn-backups/<stamp>/)
    if BACKUPS not in (op.dirs("") or set()):
        op.call("create_directory", path="", name=BACKUPS)
    op.call("create_directory", path=BACKUPS, name=stamp)
    for rel, kind, live, _ in plan:
        if kind == "text" and live is not None:
            op.call("write_file", path=backup_path(stamp, rel), content=live)
            manifest["backups"].append(rel)
        elif kind == "text":
            manifest["created"].append(rel)
    op.call("write_file", path="%s/%s/manifest.json" % (BACKUPS, stamp), content=json.dumps(manifest, indent=1))
    # 2. binaries first (CSS/HTML may reference them), then text
    binaries = [(rel, data) for rel, kind, _, data in plan if kind == "binary"]
    if binaries:
        print("binaries written:", install_binaries(op, binaries))
    for rel, kind, _, new in plan:
        if kind == "text":
            op.call("write_file", path=REMOTE_THEME + "/" + rel, content=new)
            print("written", rel)
    op.call("write_file", path=MARKER, content=head + "\n")
    op.call("purge_wordpress_cache", domain=DOMAIN)
    # 3. verify by reading everything back
    bad = [rel for rel, kind, _, new in plan
           if (op.read(REMOTE_THEME + "/" + rel) if kind == "text" else live_bytes(rel)) != new]
    if bad:
        sys.exit("Verify FAILED for %s. Roll back with: landing.py rollback %s" % (bad, stamp))
    print("Deployed %s and verified. Cache purged. Rollback id: %s" % (head[:7], stamp))


def backup_path(stamp, rel):
    return "%s/%s/%s" % (BACKUPS, stamp, rel.replace("/", "__"))


def cmd_rollback(stamp):
    op = OnePanel()
    raw = op.read("%s/%s/manifest.json" % (BACKUPS, stamp))
    if not raw:
        sys.exit("No deploy %s on the server." % stamp)
    manifest = json.loads(raw)
    for rel in manifest["backups"]:
        old = op.read(backup_path(stamp, rel))
        if old is None:
            sys.exit("Backup of %s is missing; stopping." % rel)
        op.call("write_file", path=REMOTE_THEME + "/" + rel, content=old)
        print("restored", rel)
    for rel in manifest["created"]:
        print("  new file %s was left in place (unused once the old pages are back)." % rel)
    op.call("write_file", path=MARKER, content=manifest["from"] + "\n")
    op.call("purge_wordpress_cache", domain=DOMAIN)
    print("Rolled back to %s. Binary files are not rolled back; redeploy an older commit for those." % manifest["from"][:7])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("find").add_argument("target")
    sub.add_parser("preview").add_argument("key")
    for name in ("plan", "deploy"):
        sub.add_parser(name).add_argument("--base", help="commit that is live now (only needed before the first deploy)")
    sub.add_parser("rollback").add_argument("stamp")
    args = ap.parse_args()
    if args.cmd == "rollback":
        return cmd_rollback(args.stamp)
    repo = find_repo(args.repo)
    if args.cmd == "find":
        cmd_find(repo, args.target)
    elif args.cmd == "preview":
        cmd_preview(repo, args.key)
    else:
        cmd_deploy(repo, args.base, args.cmd == "deploy")


if __name__ == "__main__":
    main()
