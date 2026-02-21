import asyncio
import os
import re
import urllib.parse
from pathlib import Path
import httpx
from playwright.async_api import async_playwright

TARGET_URL = "https://f5academy.com/"
OUTPUT_DIR = Path("cloned_site")
ASSETS_DIR = OUTPUT_DIR / "assets"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)

downloaded = {}

async def download_asset(client: httpx.AsyncClient, url: str) -> tuple[str, str]:
    if url in downloaded:
        return url, downloaded[url]
    try:
        r = await client.get(url, timeout=15)
        r.raise_for_status()
        parsed = urllib.parse.urlparse(url)
        filename = Path(parsed.path).name or "file"
        if not filename or len(filename) < 3:
            filename = f"file_{abs(hash(url)) % 99999}"
        local_name = f"{abs(hash(url)) % 99999}_{filename}"
        local_path = ASSETS_DIR / local_name
        local_path.write_bytes(r.content)
        rel_path = f"assets/{local_name}"
        downloaded[url] = rel_path
        print(f"  ✅ {filename}")
        return url, rel_path
    except Exception as e:
        print(f"  ❌ {url[-50:]}: {e}")
        return url, url

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        print("🌐 Открываем сайт...")
        await page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)

        print("📜 Прокручиваем страницу для lazy-load...")
        await page.evaluate("""
            async () => {
                await new Promise(resolve => {
                    let total = 0;
                    const timer = setInterval(() => {
                        window.scrollBy(0, 400);
                        total += 400;
                        if (total >= document.body.scrollHeight) {
                            clearInterval(timer);
                            window.scrollTo(0, 0);
                            resolve();
                        }
                    }, 150);
                });
            }
        """)
        await asyncio.sleep(3)

        html = await page.content()
        await browser.close()

    # ✅ Сразу сохраняем HTML — ДО скачивания ресурсов
    raw_html_path = OUTPUT_DIR / "index_raw.html"
    raw_html_path.write_text(html, encoding="utf-8")
    print(f"\n💾 Сырой HTML сохранён: {raw_html_path}")
    print(f"   Размер: {len(html)} символов")

    print("\n📦 Скачиваем ресурсы...")

    patterns = [
        r'src=["\']([^"\']+)["\']',
        r'href=["\']([^"\']+\.(?:css|woff|woff2|ttf|svg|png|jpg|jpeg|gif|ico))["\']',
        r'url\(["\']?([^"\')\s]+)["\']?\)',
    ]

    all_urls = set()
    for pattern in patterns:
        for match in re.findall(pattern, html):
            if match.startswith("http"):
                all_urls.add(match)
            elif match.startswith("//"):
                all_urls.add("https:" + match)

    print(f"   Найдено ресурсов: {len(all_urls)}")

    async with httpx.AsyncClient(follow_redirects=True, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    }) as client:
        tasks = [download_asset(client, url) for url in all_urls]
        results = await asyncio.gather(*tasks)

    print("\n✏️  Заменяем пути...")
    for original_url, local_path in results:
        if local_path != original_url:
            html = html.replace(f'"{original_url}"', f'"{local_path}"')
            html = html.replace(f"'{original_url}'", f"'{local_path}'")
            html = html.replace(f'({original_url})', f'({local_path})')
            # вариант без протокола
            no_proto = original_url.replace("https://", "//").replace("http://", "//")
            html = html.replace(f'"{no_proto}"', f'"{local_path}"')
            html = html.replace(f"'{no_proto}'", f"'{local_path}'")

    final_path = OUTPUT_DIR / "index.html"
    final_path.write_text(html, encoding="utf-8")

    print(f"\n🎉 Готово!")
    print(f"   index.html: {final_path.absolute()}")
    print(f"   Ресурсов скачано: {len(downloaded)}")

if __name__ == "__main__":
    asyncio.run(main())