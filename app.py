import re

import requests
import streamlit as st

from Kuula_Downloader import extract_posts, get_best_size

CDN = "https://files.kuula.io"
CDN2 = "https://d3gkeulpe5oq35.cloudfront.net"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://kuula.co/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

st.title("Kuula Panorama Downloader")
st.write("Paste any Kuula collection or post URL to download the panoramas.")

url = st.text_input("Kuula URL", placeholder="https://kuula.co/post/XXXXX")

if st.button("Fetch") and url:
    url = re.sub(r'kuula\.co/post/([A-Za-z0-9]+)', r'kuula.co/share/\1', url)

    with st.spinner("Fetching page..."):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            posts = extract_posts(resp.text)
        except Exception as e:
            st.error(f"Failed to fetch page: {e}")
            st.stop()

    if not posts:
        st.error("No panoramas found. Make sure the URL is public.")
        st.stop()

    st.success(f"Found {len(posts)} panorama(s)")

    for i, (name, uuid, sizes) in enumerate(posts, 1):
        size = get_best_size(sizes) if sizes else "8192"
        img_url = f"{CDN}/{uuid}/01-{size}.jpg"

        with st.spinner(f"Downloading {name}..."):
            try:
                r = requests.get(img_url, headers=HEADERS, timeout=60)
                r.raise_for_status()
            except Exception:
                try:
                    r = requests.get(f"{CDN2}/{uuid}/01-{size}.jpg", headers=HEADERS, timeout=60)
                    r.raise_for_status()
                except Exception as e:
                    st.warning(f"Skipped {name}: {e}")
                    continue

        st.download_button(
            label=f"Download {name}.jpg",
            data=r.content,
            file_name=f"{name}.jpg",
            mime="image/jpeg",
            key=f"dl_{i}",
        )
