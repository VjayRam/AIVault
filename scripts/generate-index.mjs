import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import crypto from 'crypto';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_ROOT = path.join(__dirname, '../components_repo');
const OUTPUT_FILE = path.join(__dirname, '../src/data/components.json');
// TODO: Replace with your actual GitHub repository URL
const GITHUB_REPO_URL = 'https://github.com/VjayRam/AIVault/tree/main/components_repo'; 

/**
 * Updates the README.md file with the component ID badge if it exists.
 * Adds badges after the title if missing, or updates existing badges.
 */
function updateReadmeWithCompId(componentDir, compId, version) {
  const readmePath = path.join(componentDir, 'README.md');
  
  if (!fs.existsSync(readmePath)) {
    return; // No README to update
  }
  
  let content = fs.readFileSync(readmePath, 'utf-8');
  
  // Escape underscores for badge URL (comp_id -> comp__id)
  const escapedCompId = compId.replace(/_/g, '__');
  const compIdBadge = `![Component ID](https://img.shields.io/badge/Component%20ID-${escapedCompId}-blue)`;
  const versionBadge = `![Version](https://img.shields.io/badge/Version-${version}-green)`;
  
  // Check if badges already exist
  const hasCompIdBadge = content.includes('![Component ID]');
  const hasVersionBadge = content.includes('![Version]');
  
  if (hasCompIdBadge) {
    // Update existing Component ID badge
    content = content.replace(
      /!\[Component ID\]\([^)]+\)/,
      compIdBadge
    );
  }
  
  if (hasVersionBadge) {
    // Update existing Version badge
    content = content.replace(
      /!\[Version\]\([^)]+\)/,
      versionBadge
    );
  }
  
  // If no badges exist, add them after the first heading
  if (!hasCompIdBadge && !hasVersionBadge) {
    // Find the first markdown heading (# Title)
    const headingMatch = content.match(/^#\s+.+$/m);
    if (headingMatch) {
      const headingEnd = content.indexOf(headingMatch[0]) + headingMatch[0].length;
      const before = content.slice(0, headingEnd);
      const after = content.slice(headingEnd);
      content = `${before}\n\n${compIdBadge}\n${versionBadge}${after}`;
    }
  } else if (!hasCompIdBadge) {
    // Add Component ID badge before Version badge
    content = content.replace(
      /!\[Version\]/,
      `${compIdBadge}\n![Version]`
    );
  } else if (!hasVersionBadge) {
    // Add Version badge after Component ID badge
    content = content.replace(
      /!\[Component ID\]\([^)]+\)/,
      `${compIdBadge}\n${versionBadge}`
    );
  }
  
  // Also update the Metadata section at the bottom if it exists
  const metadataCompIdPattern = /- \*\*Component ID\*\*:\s*`[^`]+`/;
  if (metadataCompIdPattern.test(content)) {
    content = content.replace(
      metadataCompIdPattern,
      `- **Component ID**: \`${compId}\``
    );
  }
  
  fs.writeFileSync(readmePath, content);
  console.log(`Updated README.md with comp_id for ${path.basename(componentDir)}`);
}

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
        let metadata = JSON.parse(content);
        let modified = false;

        // Assign unique component ID if missing
        if (!metadata.comp_id) {
            // Generate a short 5-character hex ID
            const shortId = crypto.randomBytes(3).toString('hex').slice(0, 5);
            metadata.comp_id = `comp_${shortId}`;
            modified = true;
        }

        // Write back to file if modified
        if (modified) {
            fs.writeFileSync(file, JSON.stringify(metadata, null, 2));
            console.log(`Assigned comp_id to ${path.basename(path.dirname(file))}`);
            
            // Update README.md with the new component ID if it exists
            updateReadmeWithCompId(path.dirname(file), metadata.comp_id, metadata.version || 'v1.0.0');
        }
        
        // Calculate relative path from REPO_ROOT
        const relativePath = path.relative(REPO_ROOT, path.dirname(file));
        // Normalize path separators for URL
        const urlPath = relativePath.split(path.sep).join('/');
        
        // Get last updated date from git
        const componentDir = path.dirname(file);
        let lastUpdated = '';
        try {
            // Check if inside git repo
            execSync('git rev-parse --is-inside-work-tree', { stdio: 'ignore' });
            lastUpdated = execSync(`git log -1 --format=%ad --date=short -- "${componentDir}"`, { encoding: 'utf-8' }).trim();
        } catch (e) {
            // Fallback to file mtime if git fails
            lastUpdated = fs.statSync(file).mtime.toISOString().split('T')[0];
        }

        return {
        ...metadata,
        path: urlPath,
        url: `${GITHUB_REPO_URL}/${urlPath}`,
        lastUpdated
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