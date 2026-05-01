const http = require("http");
const https = require("https");

const PORT = Number(process.env.PORT || 8787);
const TARGET_HOST = "dashscope.aliyuncs.com";

function setCors(res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Authorization,Content-Type,Accept,DashScope-SSE");
  res.setHeader("Access-Control-Max-Age", "86400");
}

const server = http.createServer((req, res) => {
  setCors(res);
  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  const targetPath = req.url || "/";
  const headers = { ...req.headers, host: TARGET_HOST };
  delete headers.origin;
  delete headers.referer;

  const proxyReq = https.request(
    {
      hostname: TARGET_HOST,
      port: 443,
      path: targetPath,
      method: req.method,
      headers
    },
    proxyRes => {
      setCors(res);
      const responseHeaders = { ...proxyRes.headers };
      delete responseHeaders["access-control-allow-origin"];
      delete responseHeaders["access-control-allow-methods"];
      delete responseHeaders["access-control-allow-headers"];
      res.writeHead(proxyRes.statusCode || 502, responseHeaders);
      proxyRes.pipe(res);
    }
  );

  proxyReq.on("error", err => {
    setCors(res);
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: err.message }));
  });

  req.pipe(proxyReq);
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`DashScope proxy: http://127.0.0.1:${PORT}`);
  console.log(`Use API URL: http://127.0.0.1:${PORT}/compatible-mode/v1`);
});
