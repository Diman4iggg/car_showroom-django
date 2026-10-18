// Run with Node.js and Playwright available in NODE_PATH.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

async function main() {
    const folder = path.resolve('docs/diagrams');
    const browser = await chromium.launch({ headless: true, channel: process.env.DIAGRAM_BROWSER || 'chrome' });
    try {
        const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1.5 });
        await page.setContent('<html><head><meta charset="utf-8"></head><body style="margin:0;background:white"><div id="diagram" style="display:inline-block;padding:24px"></div></body></html>');
        await page.addScriptTag({ url: 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js' });
        await page.evaluate(() => mermaid.initialize({
            startOnLoad: false,
            theme: 'neutral',
            securityLevel: 'strict',
            flowchart: { htmlLabels: false, useMaxWidth: false },
            class: { useMaxWidth: false },
            state: { useMaxWidth: false },
            themeVariables: { fontFamily: 'Arial, sans-serif', fontSize: '16px' },
        }));
        const selected = process.argv.slice(2);
        const names = fs.readdirSync(folder).filter(name => name.endsWith('.mmd') && (!selected.length || selected.includes(name))).sort();
        for (const [index, name] of names.entries()) {
            const source = fs.readFileSync(path.join(folder, name), 'utf8');
            const dimensions = await page.evaluate(async ({ source, index }) => {
                const { svg } = await mermaid.render(`diagram-${index}`, source);
                const host = document.getElementById('diagram');
                host.innerHTML = svg;
                const element = host.querySelector('svg');
                const box = element.viewBox.baseVal;
                element.style.maxWidth = 'none';
                element.setAttribute('width', Math.ceil(box.width));
                element.setAttribute('height', Math.ceil(box.height));
                await document.fonts.ready;
                return { width: Math.ceil(box.width), height: Math.ceil(box.height) };
            }, { source, index });
            const output = path.join(folder, name.replace(/\.mmd$/, '.png'));
            await page.locator('#diagram').screenshot({ path: output, timeout: 60000 });
            console.log(`${name}: ${dimensions.width}x${dimensions.height} -> ${path.basename(output)}`);
        }
    } finally {
        await browser.close();
    }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
