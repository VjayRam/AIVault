import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_ROOT = path.join(__dirname, '../components_repo');

function getDirectories(srcPath) {
  return fs.readdirSync(srcPath).filter(file => {
    return fs.statSync(path.join(srcPath, file)).isDirectory();
  });
}

function bumpVersion(version, type) {
    // Remove 'v' prefix if present
    const cleanVersion = version.toLowerCase().startsWith('v') ? version.slice(1) : version;
    const parts = cleanVersion.split('.').map(Number);
    
    if (parts.length !== 3 || parts.some(isNaN)) {
        console.warn(`Invalid version format: ${version}. Resetting to 1.0.0`);
        return 'v1.0.0';
    }

    if (type === 'major') {
        parts[0]++;
        parts[1] = 0;
        parts[2] = 0;
    } else if (type === 'minor') {
        parts[1]++;
        parts[2] = 0;
    } else if (type === 'patch') {
        parts[2]++;
    }
    
    return `v${parts.join('.')}`;
}

function getBumpType(messages, compId) {
    let type = null;
    for (const msg of messages) {
        // Only consider commits that start with the component ID
        if (!compId || !msg.startsWith(compId)) {
            continue;
        }

        // Extract the content after the comp_id
        let content = msg.slice(compId.length).trim();
        // Handle common separators like ": " or " "
        if (content.startsWith(':')) content = content.slice(1).trim();
        if (content.startsWith('-')) content = content.slice(1).trim();

        if (content.includes('BREAKING CHANGE') || content.includes('!:')) {
            return 'major';
        }
        
        if (content.startsWith('feat')) {
            type = 'minor';
        } else if (content.startsWith('fix')) {
            if (type !== 'minor') type = 'patch';
        } else {
            // If comp_id is present but no specific type, assume patch
            if (type === null) type = 'patch';
        }
    }
    return type;
}

function updateVersions() {
    if (!fs.existsSync(REPO_ROOT)) {
        console.error(`Directory not found: ${REPO_ROOT}`);
        return;
    }

    // Check if inside git repo
    try {
        execSync('git rev-parse --is-inside-work-tree', { stdio: 'ignore' });
    } catch (e) {
        console.error('Not a git repository. Cannot determine version updates.');
        return;
    }

    const components = getDirectories(REPO_ROOT);
    let updatedCount = 0;

    for (const componentName of components) {
        const componentDir = path.join(REPO_ROOT, componentName);
        const metadataFile = path.join(componentDir, 'metadata.json');

        if (!fs.existsSync(metadataFile)) {
            continue;
        }

        try {
            const content = fs.readFileSync(metadataFile, 'utf-8');
            const metadata = JSON.parse(content);
            const currentVersion = metadata.version || 'v0.0.0';
            const compId = metadata.comp_id;

            // 1. Find the last commit that modified metadata.json
            // We use relative path for git commands
            const relMetadataPath = path.relative(path.join(__dirname, '..'), metadataFile).replace(/\\/g, '/');
            const relComponentPath = path.relative(path.join(__dirname, '..'), componentDir).replace(/\\/g, '/');

            let lastMetaHash = '';
            try {
                lastMetaHash = execSync(`git log -n 1 --format=%H -- "${relMetadataPath}"`, { encoding: 'utf-8' }).trim();
            } catch (e) {
                // File might be new and not committed yet
            }

            let messages = [];
            if (lastMetaHash) {
                // Get commits affecting the component folder since the last metadata change
                // We exclude the commit that changed metadata.json itself to avoid loops if we commit automatically
                const logCmd = `git log --format="%s" ${lastMetaHash}..HEAD -- "${relComponentPath}"`;
                try {
                    const output = execSync(logCmd, { encoding: 'utf-8' });
                    messages = output.split('\n').filter(Boolean);
                } catch (e) {
                    console.warn(`Could not get git log for ${componentName}: ${e.message}`);
                }
            } else {
                // If metadata.json has no history, check all history for the component
                 try {
                    const output = execSync(`git log --format="%s" -- "${relComponentPath}"`, { encoding: 'utf-8' });
                    messages = output.split('\n').filter(Boolean);
                } catch (e) {}
            }

            if (messages.length === 0) {
                continue;
            }

            const bumpType = getBumpType(messages, compId);
            
            if (bumpType) {
                const newVersion = bumpVersion(currentVersion, bumpType);
                if (newVersion !== currentVersion) {
                    console.log(`[${componentName}] Bumping version: ${currentVersion} -> ${newVersion} (${bumpType})`);
                    console.log(`  Reasons: ${messages.slice(0, 3).join(', ')}${messages.length > 3 ? '...' : ''}`);
                    
                    metadata.version = newVersion;
                    fs.writeFileSync(metadataFile, JSON.stringify(metadata, null, 2));
                    updatedCount++;
                }
            }

        } catch (e) {
            console.error(`Error processing ${componentName}:`, e);
        }
    }

    if (updatedCount > 0) {
        console.log(`Updated versions for ${updatedCount} components.`);
        console.log('Please review changes and commit metadata.json files.');
    } else {
        console.log('No version updates needed.');
    }
}

updateVersions();
