# Kuula Downloader

A lightweight Python script to download full-resolution panoramic images from any public Kuula collection or post.

## Features

- Works with any public Kuula URL (collections, posts, or share links)
- Automatically selects the highest available resolution
- Skips already-downloaded images
- Falls back to a secondary CDN if the primary fails

## Requirements

- Python 3.7+
- [requests](https://pypi.org/project/requests/) library

Install dependencies:

```bash
pip install requests

Usage
python Kuula_Downloader.py <kuula_url> [output_dir]

Supported URL Formats
Format	Example
Collection	https://kuula.co/share/XXXXX/collection/YYYYY
Share link	https://kuula.co/share/XXXXX
Post link	https://kuula.co/post/XXXXX

Output
Images are saved as .jpg files named after their title (e.g. 01_Entrance.jpg, 02_Oval.jpg). If a post has no title, it falls back to 01_post_01.jpg.

License
MIT
