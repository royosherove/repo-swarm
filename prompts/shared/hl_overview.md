version=2
## Repository Structure and Files

{repo_structure}
---

Act as a senior software architect tasked with understanding this new project. Analyze the entire workspace.
Please provide a concise summary covering:
0. **Repository Name:** Write the name of the repository or the project name. if you can't find it, or if you are not sure, output: NOT_FAOUND. IMPORTANT: the format of the output should be: [[repository name]]
1.  **Project Purpose:** What problem does this project seem to solve? What is its primary domain?
2. **Architecture Pattern**: The overall architectural pattern or patterns used
3.  **Technology Stack:** Identify the primary programming languages, frameworks, and any major libraries or dependencies suggested by the configuration/package files. **For Python projects specifically**: Examine requirements.txt, pyproject.toml, setup.py, setup.cfg, Pipfile, and poetry.lock files to identify all Python dependencies, their versions, and purposes.

**Note**: When looking for dependencies, package names, or library names, perform case-insensitive matching and consider variations with dashes between words (e.g., "new-relic", "data-dog", "express-rate-limit").
4.  **Initial Structure Impression:** Based on the root directory structure, what seem to be the main high-level parts of this application (e.g., frontend, backend, workers, libraries)?
5. **configuration/package**: identify and list all configuration or package files
6.  **Directory Structure:** Describe the purpose of all the source code directories and how the code appears to be organized (e.g., by feature, by layer).
7.  **High-Level Architecture:** What architectural pattern(s) seem to be employed (e.g., Layered, MVC, Microservices, Event-Driven)? What evidence supports this (e.g., specific directories, framework usage, communication patterns)?
8.  **Build, Execution and Test:** How is the project typically built, run and tested, based on the available scripts and configuration files? Identify the main entry point(s) if possible.

**Special Instruction:** ignore any files under 'arch-docs' folder.

Format the output clearly using markdown
