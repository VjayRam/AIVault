# Project Governance & Safety

To ensure the stability and security of **AIVault**, we enforce the following governance rules and safety measures.

## 🛡️ Branch Protection Rules

Since we cannot automate the setting of these rules via code, the repository administrator must enable them manually in the GitHub Repository Settings.

**Go to:** `Settings` -> `Branches` -> `Add branch protection rule` -> `main`

### Recommended Configuration:

1.  **Require a pull request before merging**
    *   [x] **Require approvals**: Set to at least `1`.
    *   [x] **Dismiss stale pull request approvals when new commits are pushed**.
    *   [x] **Require review from Code Owners**: Ensures that changes to critical areas (like `components_repo`) are reviewed by the designated owners defined in `.github/CODEOWNERS`.

2.  **Require status checks to pass before merging**
    *   [x] **Require branches to be up to date before merging**.
    *   **Status check to select**: `validate-build` (This comes from our `.github/workflows/ci.yml`).
    *   *Why?* This prevents broken code that fails to build from ever reaching the main branch.

3.  **Include administrators**
    *   [x] **Enforce all configured restrictions for administrators**.
    *   *Why?* Prevents accidental direct commits even by the owner.

## 👥 Code Owners

We use a `CODEOWNERS` file located at `.github/CODEOWNERS` to automatically request reviews from the right people.

*   **Global Owner**: @VjayRam
*   **Critical Paths**: Changes to `/scripts/` or `/components_repo/` require explicit approval from the maintainer.

## 🤖 CI/CD Safety

We have configured a GitHub Action (`.github/workflows/ci.yml`) that runs on every Pull Request. It performs the following safety checks:
1.  **Dependency Installation**: Ensures `npm ci` works.
2.  **Index Generation**: Verifies that `generate-index.mjs` runs without error.
3.  **Changelog Generation**: Verifies that `generate-changelog.mjs` runs without error.
4.  **Build Verification**: Ensures the Astro site builds successfully (`npm run build`).

## 🔒 Secret Management

*   **Never commit secrets**: The `.gitignore` is configured to exclude `.env` files and private keys.
*   **GitHub Secrets**: Use GitHub Repository Secrets for any API keys or tokens needed in CI/CD.
