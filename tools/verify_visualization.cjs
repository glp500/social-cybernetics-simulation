#!/usr/bin/env node
"use strict";

const { spawn } = require("node:child_process");
const net = require("node:net");
const path = require("node:path");
const process = require("node:process");

const ROOT = path.resolve(__dirname, "..");
const SCREENSHOT = path.join(ROOT, "docs", "solara-v0.2.png");
const PLAYWRIGHT = path.join(process.env.CONDA_PREFIX, "lib", "node_modules", "playwright");
const { chromium } = require(PLAYWRIGHT);
const LEGACY_VUE_WARNING =
  "Failed to evaluate Vue script and find module.exports, falling back to old method";

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function availablePort() {
  const server = net.createServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  await new Promise((resolve) => server.close(resolve));
  if (!address || typeof address === "string") throw new Error("Could not allocate a local port");
  return address.port;
}

async function waitForServer(child, logs, url) {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    if (child.exitCode !== null) {
      throw new Error(`Solara exited early:\n${logs.join("")}`);
    }
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // The server is still starting.
    }
    await delay(250);
  }
  throw new Error("Solara did not become ready within 30 seconds");
}

async function verifyPage(page, url) {
  const browserProblems = [];
  const upstreamWarnings = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      const location = message.location();
      const source = location.url ? ` (${location.url}:${location.lineNumber})` : "";
      const description = `console ${message.type()}: ${message.text()}${source}`;
      const isKnownUpstreamWarning =
        message.type() === "warning" &&
        message.text().includes(LEGACY_VUE_WARNING) &&
        location.url.includes("/jupyter/nbextensions/jupyter-vue/nodeps.js");
      (isKnownUpstreamWarning ? upstreamWarnings : browserProblems).push(description);
    }
  });
  page.on("pageerror", (error) => browserProblems.push(`page error: ${error}`));

  await page.goto(url, { waitUntil: "networkidle", timeout: 60_000 });
  try {
    await page.getByText("Social Cybernetics Sugarscape").waitFor();
    await page.getByText("Total resources").waitFor();
    await page.getByText("Recovering cells").waitFor();
    await page.getByText("Active shock events").waitFor();
    await page.getByText("Cells damaged this tick").waitFor();
    await page.waitForFunction(() => document.body.innerText.includes("25.000"));
    await page.getByRole("button", { name: "Step", exact: true }).click();
    await page.waitForFunction(() => !document.body.innerText.includes("25.000"));
    await page.waitForFunction(() => document.body.innerText.includes("11.000"));
  } catch (error) {
    const body = await page.locator("body").innerText();
    throw new Error(`${error}\n${browserProblems.join("\n")}\nRendered body:\n${body}`);
  }
  await page.screenshot({ path: SCREENSHOT, fullPage: true });
  return { browserProblems, upstreamWarnings };
}

async function main() {
  const logs = [];
  let allowedUpstreamWarnings = 0;
  const port = await availablePort();
  const url = `http://127.0.0.1:${port}/`;
  const environment = {
    ...process.env,
    IPYTHONDIR: "/tmp/scs-ipython",
    MPLCONFIGDIR: "/tmp/scs-mpl",
    PYTHONPATH: path.join(ROOT, "src"),
    SOLARA_SESSION_HTTPS_ONLY: "false",
    XDG_CACHE_HOME: "/tmp/scs-cache",
  };
  const python = path.join(process.env.CONDA_PREFIX, "bin", "python");
  const child = spawn(
    python,
    [
      "-m",
      "solara",
      "run",
      "src/social_cybernetics/runtime/mesa/app.py",
      "--host",
      "127.0.0.1",
      "--port",
      String(port),
    ],
    { cwd: ROOT, env: environment, stdio: ["ignore", "pipe", "pipe"] },
  );
  child.stdout.on("data", (data) => logs.push(data.toString()));
  child.stderr.on("data", (data) => logs.push(data.toString()));

  try {
    await waitForServer(child, logs, url);
    const browser = await chromium.launch({ headless: true });
    try {
      const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
      const page = await context.newPage();
      const { browserProblems, upstreamWarnings } = await verifyPage(page, url);
      if (browserProblems.length) throw new Error(browserProblems.join("\n"));
      if (upstreamWarnings.length > 1) {
        throw new Error(`unexpected repeated upstream warnings:\n${upstreamWarnings.join("\n")}`);
      }
      allowedUpstreamWarnings = upstreamWarnings.length;
    } finally {
      await browser.close();
    }
  } finally {
    child.kill("SIGTERM");
    await Promise.race([new Promise((resolve) => child.once("exit", resolve)), delay(10_000)]);
    if (child.exitCode === null) child.kill("SIGKILL");
  }

  console.log(
    `visualization verified; screenshot: ${path.relative(ROOT, SCREENSHOT)}; ` +
      `known upstream warnings: ${allowedUpstreamWarnings}`,
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
