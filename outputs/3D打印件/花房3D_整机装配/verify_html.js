const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch({
    args: ['--enable-unsafe-swiftshader', '--use-gl=angle', '--use-angle=swiftshader', '--ignore-gpu-blocklist']
  });
  const page = await browser.newPage({ viewport: { width: 1480, height: 900 } });
  const errs = [];
  page.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text()); });
  const url = 'file:///' + encodeURI(path.resolve('花房整机示意模型.html').replace(/\\/g, '/'));
  await page.goto(url);
  await page.waitForTimeout(2200);
  // WebGL 上下文与绘制调用是否成功
  const info = await page.evaluate(() => {
    const c = document.getElementById('c');
    const gl = c.getContext('webgl');
    return {
      canvas: c.width + 'x' + c.height,
      webgl: !!gl,
      renderer: gl ? gl.getParameter(gl.RENDERER) : null,
      tri: (document.getElementById('stat').textContent || '').trim().slice(0, 40),
      legend: document.querySelectorAll('.legend li').length,
    };
  });
  console.log('INFO', JSON.stringify(info, null, 1));
  await page.screenshot({ path: 'preview/00_HTML验证_轴测.png' });
  // 切到俯视再截一张，验证按钮与重绘
  await page.click('button[data-v="top"]');
  await page.waitForTimeout(900);
  await page.screenshot({ path: 'preview/00_HTML验证_俯视.png' });
  console.log(errs.length ? errs.join('\n') : '无 JS 错误');
  await browser.close();
})();
