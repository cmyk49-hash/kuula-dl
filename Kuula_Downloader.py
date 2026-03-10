"""
Kuula panorama downloader.
Works with any Kuula collection or single post URL.

Usage:
    python download_panoramas.py <kuula_url> [output_dir]
"""

import base64
import json
import os
import re
import sys
import requests

CDN = "https://files.kuula.io"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://kuula.co/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def decode_kuula_var(html, var_name):
    """Extract and base64-decode a Kuula JS window variable."""
    pattern = rf'window\.{var_name}\s*=\s*\{{[^}}]*data\s*:\s*"([A-Za-z0-9+/=]+)"'
    m = re.search(pattern, html)
    if m:
        try:
            return json.loads(base64.b64decode(m.group(1)).decode("utf-8"))
        except Exception as e:
            print(f"  Warning: failed to decode {var_name}: {e}")
    return None


def get_best_size(sizes):
    """Return the highest resolution size from a list like ['8192', '4096']."""
    priority = ["8192", "4096", "2048", "1024", "full", "8k", "4k"]
    for s in priority:
        if s in sizes:
            return s
    return sizes[0] if sizes else "8192"


def extract_posts(html):
    """Return a list of (name, uuid, sizes) tuples from the page HTML."""
    posts = []

    # Try collection first
    col = decode_kuula_var(html, "KUULA_COLLECTION")
    if col and "posts" in col:
        for i, post in enumerate(col["posts"], 1):
            uuid = post.get("uuid", "")
            desc = post.get("description", "") or f"post_{i}"
            name = f"{i:02d}_{re.sub(r'[^A-Za-z0-9_]+', '_', desc).strip('_')}"
            sizes = []
            photos = post.get("photos", [])
            if photos:
                sizes = photos[0].get("sizes", [])
            posts.append((name, uuid, sizes))
        return posts

    # Fall back to single post
    post_data = decode_kuula_var(html, "KUULA_POST")
    if post_data:
        uuid = post_data.get("uuid", "")
        desc = post_data.get("description", "") or "post_01"
        name = f"01_{re.sub(r'[^A-Za-z0-9_]+', '_', desc).strip('_')}"
        sizes = []
        photos = post_data.get("photos", [])
        if photos:
            sizes = photos[0].get("sizes", [])
        posts.append((name, uuid, sizes))
        return posts

    return []


def download_image(url, dest, session):
    r = session.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)
    return os.path.getsize(dest)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "panoramas")
    os.makedirs(output_dir, exist_ok=True)

    # Normalize /post/{id} -> /share/{id} so KUULA_POST data is available
    url = re.sub(r'kuula\.co/post/([A-Za-z0-9]+)', r'kuula.co/share/\1', url)

    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"Fetching: {url}")
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    html = resp.text

    posts = extract_posts(html)
    if not posts:
        print("ERROR: Could not find any posts in the page.")
        print("  Make sure the URL is a public Kuula collection or post.")
        sys.exit(1)

    print(f"Found {len(posts)} panorama(s)\n")

    total = len(posts)
    for i, (name, uuid, sizes) in enumerate(posts, 1):
        dest = os.path.join(output_dir, f"{name}.jpg")

        if os.path.exists(dest):
            mb = os.path.getsize(dest) / 1_048_576
            print(f"[{i}/{total}] SKIP  {name}  ({mb:.1f} MB)")
            continue

        size = get_best_size(sizes) if sizes else "8192"
        img_url = f"{CDN}/{uuid}/01-{size}.jpg"

        print(f"[{i}/{total}] {name}  ({size}px) ...", end=" ", flush=True)
        try:
            mb = download_image(img_url, dest, session) / 1_048_576
            print(f"OK  ({mb:.1f} MB)")
        except requests.HTTPError as e:
            print(f"FAILED ({e})")
            # Try the other CDN as fallback
            fallback = f"https://d3gkeulpe5oq35.cloudfront.net/{uuid}/01-{size}.jpg"
            print(f"  Trying fallback CDN ...", end=" ", flush=True)
            try:
                mb = download_image(fallback, dest, session) / 1_048_576
                print(f"OK  ({mb:.1f} MB)")
            except Exception as e2:
                if os.path.exists(dest):
                    os.remove(dest)
                print(f"FAILED ({e2})")
        except Exception as e:
            if os.path.exists(dest):
                os.remove(dest)
            print(f"FAILED ({e})")

    print(f"\nDone. Images saved to: {output_dir}")


if __name__ == "__main__":
    main()
