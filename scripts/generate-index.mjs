import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_ROOT = path.join(__dirname, '../components_repo');
const OUTPUT_FILE = path.join(__dirname, '../src/data/components.json');
// TODO: Replace with your actual GitHub repository URL
const GITHUB_REPO_URL = 'https://github.com/VjayRam/ReuseAI/tree/main/components_repo'; 

function getFiles(dir) {
  const subdirs = fs.readdirSync(dir);
  const files = subdirs.map((subdir) => {
    const res = path.resolve(dir, subdir);
    return fs.statSync(res).isDirectory() ? getFiles(res) : res;
  });
  return files.reduce((a, f) => a.concat(f), []);
}

function generateIndex() {
  if (!fs.existsSync(REPO_ROOT)) {
    console.error(`Directory not found: ${REPO_ROOT}`);
    return;
  }

  const allFiles = getFiles(REPO_ROOT);
  const metadataFiles = allFiles.filter((file) => file.endsWith('metadata.json'));

  const components = metadataFiles.map((file) => {
    const content = fs.readFileSync(file, 'utf-8');
    try {
        const metadata = JSON.parse(content);
        
        // Calculate relative path from REPO_ROOT
        const relativePath = path.relative(REPO_ROOT, path.dirname(file));
        // Normalize path separators for URL
        const urlPath = relativePath.split(path.sep).join('/');
        
        return {
        ...metadata,
        path: urlPath,
        url: `${GITHUB_REPO_URL}/${urlPath}`
        };
    } catch (e) {
        console.error(`Error parsing ${file}:`, e);
        return null;
    }
  }).filter(Boolean);

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(components, null, 2));
  console.log(`Generated index with ${components.length} components.`);
}

generateIndex();