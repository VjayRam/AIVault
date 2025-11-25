# Contributing to AIVault

Thank you for your interest in contributing to AIVault! We welcome contributions of all kinds, from adding new AI components to improving the website's code.

## 🧩 Adding a New Component

The core of AIVault is its library of reusable AI components. Adding a new one is easy:

1.  **Fork the Repository**: Create your own fork of the project.
2.  **Create a Folder**: Navigate to `components_repo/` and create a new folder for your component. You can organize it into subfolders (e.g., `llm-agents/my-new-agent`).
3.  **Add Your Code**: Place your component's source code, documentation, and examples in this folder.
4.  **Add Metadata**: **Crucial Step!** You must create a `metadata.json` file in your component's root folder. This file tells the website how to display your component.

    **`metadata.json` Format:**
    ```json
    {
      "name": "My New Agent",
      "description": "A brief description of what this component does.",
      "tags": ["llm", "agent", "python"],
      "author": "Your Name or GitHub Handle",
      "version": "1.0.0"
    }
    ```
5.  **Add Yourself to Contributors**: Open `CONTRIBUTORS.md` and add a new object to the JSON array with your details:
    ```json
    {
      "name": "Your Name",
      "role": "Contributor",
      "email": "your@email.com",
      "linkedin": "optional-url",
      "location": "City, Country"
    }
    ```
6.  **Submit a Pull Request**: Push your changes and open a PR to the `main` branch.

## 💻 Improving the Website

If you want to work on the frontend (Astro/React):

1.  **Install Dependencies**:
    ```bash
    npm install
    ```
2.  **Run Development Server**:
    ```bash
    npm run dev
    ```
    This will start the server at `http://localhost:4321`.
3.  **Make Changes**: The source code is in the `src/` directory.
4.  **Test**: Ensure the site builds correctly with `npm run build`.

## 🐞 Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub.

Thank you for helping us build the best resource for reusable AI components!