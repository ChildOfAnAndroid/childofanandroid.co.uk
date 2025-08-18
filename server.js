import { createServer } from 'http';
import { readdir, readFile } from 'fs/promises';
import path from 'path';

const storageDir = path.join(process.cwd(), 'storage');

async function readAll(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const result = {};
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      result[entry.name] = await readAll(fullPath);
    } else {
      result[entry.name] = await readFile(fullPath, 'utf-8');
    }
  }
  return result;
}

const server = createServer(async (req, res) => {
  if (req.method === 'GET' && req.url === '/api/files') {
    try {
      const data = await readAll(storageDir);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(data));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

const PORT = 3000;
server.listen(PORT, () => {
  console.log(`server listening on http://localhost:${PORT}`);
});