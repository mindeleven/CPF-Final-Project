# Migration files for CPF Final Project

This directory contains files and code example that have the purpose to facilitate a transition of project planning and organization from the Claude.ai browser interface to the Claude Code command line.

## 1st Step - Migration to Claude Code

This text is temporarily stored in migration/README.md

The workflow so far in this project was that I did the project planning with Claude.ai in the browser, including verbose project discussions. The Claude.ai chat interface then created specification files (stored under docs/specification) that I pasted in here for you to do the coding job. After successful coding by Claude Code on the terminal, the Claude.ai chat interface created the handoff files (stored under docs/handoff) and an update of the project progress (docs/project-progress.md). The bottleneck of this way of working was the context window of the chat interface. To avoid it, that context will get lost I'm moving the described workflow into the terminal and have it handled by Claude Code. I still have to figure out how to do this, so I'll need some feedback from time to time which resembles human interaction like in the chat interface (the more we proceed, the less this will be necessary).

As a first step I want you to read the document migration/MIGRATION-TO-CLAUDE-CODE.md. If it is necessary to create context files like it is suggested in this document, please do it and prepare some for `git commit`.

The next document I want you to read is migration/01-state-of-project-20260216/NEXT-IMPLEMENTATION-STEP-INSTRUCTIONS.md. I tried to put together to my best knowledge what's necessary to know to proceed with the project. 

After you've confirmed that we can continue working like this, I want you to implement specification spec-07E-specification.md.



