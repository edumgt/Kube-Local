#!/usr/bin/env node
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const FE_URL = process.env.FE_URL || 'http://192.168.253.148';
const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');

function getDateStamp() {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const HH = String(now.getHours()).padStart(2, '0');
  const MM = String(now.getMinutes()).padStart(2, '0');
  const SS = String(now.getSeconds()).padStart(2, '0');
  return `${yyyy}${mm}${dd}_${HH}${MM}${SS}`;
}

(async () => {
  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  try {
    console.log(`[screenshot] ${FE_URL} 접속 중...`);
    await page.goto(FE_URL, { waitUntil: 'networkidle' });

    const filename = `${getDateStamp()}.png`;
    const filepath = path.join(SCREENSHOTS_DIR, filename);

    await page.screenshot({ path: filepath, fullPage: true });
    console.log(`[screenshot] 저장 완료: screenshots/${filename}`);
  } catch (err) {
    console.error(`[screenshot] 오류: ${err.message}`);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
