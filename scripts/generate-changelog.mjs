import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COMPONENTS_DATA = path.join(__dirname, '../src/data/components.json');
const OUTPUT_FILE = path.join(__dirname, '../src/data/changelog.json');

// Helper to get component details from the generated components.json
let componentsMap = new Map();
if (fs.existsSync(COMPONENTS_DATA)) {
    try {
        const data = JSON.parse(fs.readFileSync(COMPONENTS_DATA, 'utf-8'));
        data.forEach(c => componentsMap.set(c.path, c));
    } catch (e) {
        console.error("Error reading components.json:", e);
    }
}

try {
    // Check if git is available and inside a repo
    execSync('git rev-parse --is-inside-work-tree', { stdio: 'ignore' });

    // Get commits affecting components_repo
    // Format: Hash | Author | Date | Message
    // We look for changes in the components_repo directory
    const logOutput = execSync('git log --pretty=format:"%H|%an|%ad|%s" --date=short -- components_repo', { encoding: 'utf-8' });
    
    const commits = logOutput.split('\n').filter(Boolean).map(line => {
        const parts = line.split('|');
        if (parts.length < 4) return null;
        const [hash, author, date, message] = parts;
        return { hash, author, date, message, components: [] };
    }).filter(Boolean);

    for (const commit of commits) {
        // Get files changed in this commit
        try {
            const filesOutput = execSync(`git show --name-only --pretty="" ${commit.hash}`, { encoding: 'utf-8' });
            const files = filesOutput.split('\n').filter(Boolean);
            
            const affectedComponents = new Set();

            files.forEach(file => {
                // Check if file is in components_repo
                // We expect file paths like: components_repo/category/component-name/file.ext
                const normalizedFile = file.replace(/\\/g, '/');
                if (normalizedFile.includes('components_repo/')) {
                    const parts = normalizedFile.split('/');
                    const repoIndex = parts.indexOf('components_repo');
                    if (repoIndex !== -1 && parts.length > repoIndex + 2) {
                        // components_repo/category/component-name/...
                        const category = parts[repoIndex + 1];
                        const name = parts[repoIndex + 2];
                        const componentPath = `${category}/${name}`;
                        affectedComponents.add(componentPath);
                    }
                }
            });

            commit.components = Array.from(affectedComponents).map(compPath => {
                const info = componentsMap.get(compPath);
                return {
                    path: compPath,
                    name: info ? info.name : compPath.split('/').pop(), // Fallback to folder name
                    version: info ? info.version : null,
                    componentAuthor: info ? info.author : null
                };
            });
        } catch (e) {
            console.error(`Error processing commit ${commit.hash}:`, e);
        }
    }

    // Filter out commits that didn't touch a specific component
    const relevantCommits = commits.filter(c => c.components.length > 0);

    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(relevantCommits, null, 2));
    console.log(`Generated changelog with ${relevantCommits.length} entries.`);

} catch (error) {
    console.warn('Warning: Could not generate changelog from git history. This is expected during initial setup or if not in a git repo.');
    console.warn(error.message);
    // Write empty array if git fails
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify([], null, 2));
}