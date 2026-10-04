// Creates the synthetic raster input independently of PowerPoint or reconstruction specs.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {chromium} from 'playwright';

const directory = path.dirname(fileURLToPath(import.meta.url));
const output = path.resolve(process.argv[2] ?? path.join(directory, 'source.png'));
try { await fs.access(output); throw new Error('Source exists; choose a new output.'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const browser = await chromium.launch({headless: true, ...(process.env.SLIDETHAW_BROWSER_CHANNEL ? {channel: process.env.SLIDETHAW_BROWSER_CHANNEL} : {})});
try {
  const page = await browser.newPage({viewport: {width: 1280, height: 720}, deviceScaleFactor: 1});
  await page.goto(pathToFileURL(path.join(directory, 'source.html')).href);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({path: output});
} finally { await browser.close(); }
