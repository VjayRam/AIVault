# AIVault (ReuseAI)

**AIVault** is a centralized repository for reusable AI components, designed to streamline the development of intelligent applications. Our goal is to provide developers with high-quality, tested building blocks—from LLM agents to RAG systems—that can be easily integrated into new projects.

By fostering a community of sharing and reuse, we aim to accelerate innovation in the AI space and reduce the redundancy of rebuilding common AI patterns.

## 🚀 Features

*   **Component Directory**: Browse a curated list of AI components.
*   **Smart Search**: Filter components by tags, authors, or search by keywords.
*   **Automated Indexing**: The website automatically updates when new components are added to the repository.
*   **Direct Access**: One-click access to the source code of each component on GitHub.

## 🛠️ Tech Stack

*   **Frontend**: [Astro](https://astro.build/) (Static Site Generator)
*   **UI Framework**: [React](https://react.dev/) & [Tailwind CSS](https://tailwindcss.com/)
*   **Search**: [Fuse.js](https://www.fusejs.io/) (Client-side fuzzy search)
*   **Deployment**: Vercel (Auto-builds on commit)

## 📂 Project Structure

```text
/
├── components_repo/       # The source of truth for all AI components
│   ├── llm-agents/
│   ├── rag-systems/
│   └── ...
├── src/
│   ├── components/        # React UI components (Search, Navbar)
│   ├── data/              # Generated components.json index
│   └── pages/             # Astro pages (Home, About)
├── scripts/
│   └── generate-index.mjs # Script to scan components_repo and build the index
└── public/                # Static assets (Logo, favicon)
```

## 🧞 Commands

All commands are run from the root of the project:

| Command | Action |
| :--- | :--- |
| `npm install` | Installs dependencies |
| `npm run dev` | Starts local dev server at `localhost:4321` (auto-indexes components) |
| `npm run build` | Build your production site to `./dist/` |
| `npm run preview` | Preview your build locally |

## 🤝 Contributing

We welcome contributions from the community! Whether you want to add a new AI component, improve the website, or fix a bug, we'd love your help.

👉 **[Read our Contribution Guide](CONTRIBUTING.md)** to get started.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
