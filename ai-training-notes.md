# AI Fluency: Framework and Foundations

## Index

- [AI Fluency: Framework and Foundations](#ai-fluency-framework-and-foundations)
  - [Introduction to AI Fluency](#introduction-to-ai-fluency)
  - [The 4Ds Framework](#the-4ds-framework)
  - [Delegation — Deciding What AI Should Do](#delegation--deciding-what-ai-should-do)
  - [Description — Communicating Effectively With AI](#description--communicating-effectively-with-ai)
  - [Discernment — Evaluating AI's Work](#discernment--evaluating-ais-work)
  - [The Description–Discernment Loop](#the-descriptiondiscernment-loop)
  - [Diligence — Responsible AI Collaboration](#diligence--responsible-ai-collaboration)

- [AI Capabilities and Limitations](#ai-capabilities-and-limitations)
  - [Introduction to AI Capabilities and Limitations](#introduction-to-ai-capabilities-and-limitations)
  - [What We Mean by AI](#what-we-mean-by-ai)
  - [How AI Gets Its Character](#how-ai-gets-its-character)
  - [Next Token Prediction](#next-token-prediction)
  - [Knowledge](#knowledge)
  - [Working Memory](#working-memory)
  - [Steerability](#steerability)

- [The AI-native SDLC Playbook](#the-ai-native-sdlc-playbook)
  - [Introduction: Why the SDLC Has to Change](#introduction-why-the-sdlc-has-to-change)
  - [Stage 1 Plan: Capture as intent.md](#stage-1-plan-capture-as-intentmd)
  - [Stage 2 Design: Requirements and Design](#stage-2-design-requirements-and-design)
  - [Stage 3 Build: Plan Mode as the Default Starting Point](#stage-3-build-plan-mode-as-the-default-starting-point)
  - [Stage 3 Build: The CLAUDE.md](#stage-3-build-the-claudemd)
  - [Stage 3 Build: Skills as Institutional Knowledge](#stage-3-build-skills-as-institutional-knowledge)
  - [Stage 3 Build: Parallel Sessions and Subagents](#stage-3-build-parallel-sessions-and-subagents)
  - [Stage 4 Test: Give Claude a Feedback Loop](#stage-4-test-give-claude-a-feedback-loop)
  - [Stage 4 Test: Continuous Evals in CI](#stage-4-test-continuous-evals-in-ci)
  - [Stage 5 Deploy: AI in the PR Review Loop](#stage-5-deploy-ai-in-the-pr-review-loop)
  - [Stage 5 Deploy: Hooks as Approval Gates](#stage-5-deploy-hooks-as-approval-gates)
  - [Stage 5 Deploy: CI/CD Integration and Deployment](#stage-5-deploy-cicd-integration-and-deployment)
  - [Stage 6 Maintain: Closing the Loop on Metrics](#stage-6-maintain-closing-the-loop-on-metrics)
  - [Closing: Play Dependencies and Resources](#closing-play-dependencies-and-resources)
  - [Putting It All Together: The End-to-End Loop](#putting-it-all-together-the-end-to-end-loop)

- [Claude Code in Action](#claude-code-in-action)
  - [Introduction: From Single Prompts to Hands-Off Sessions](#introduction-from-single-prompts-to-hands-off-sessions)
  - [Steering Long Sessions](#steering-long-sessions)
  - [A CLAUDE.md That Gets Followed](#a-claudemd-that-gets-followed)
  - [Verification Skills](#verification-skills)
  - [Permission Modes](#permission-modes)
  - [Hooks](#hooks)
  - [Routines and Headless Mode](#routines-and-headless-mode)
  - [GitHub Actions and Code Review](#github-actions-and-code-review)
  - [Trust It: Verifying Unsupervised Runs](#trust-it-verifying-unsupervised-runs)
  - [Plugins](#plugins)
  - [Putting It All Together: A Trusted Hands-Off Workflow](#putting-it-all-together-a-trusted-hands-off-workflow)

- [Building with the Claude API](#building-with-the-claude-api)
  - [Introduction: Building Applications on the Claude API](#introduction-building-applications-on-the-claude-api)
  - [Accessing Claude with the API](#accessing-claude-with-the-api)
  - [Prompt Evaluation](#prompt-evaluation)
  - [Prompt Engineering Techniques](#prompt-engineering-techniques)
  - [Tool Use with Claude](#tool-use-with-claude)
  - [RAG and Agentic Search](#rag-and-agentic-search)
  - [Features of Claude](#features-of-claude)
  - [Prompt Caching](#prompt-caching)
  - [Model Context Protocol](#model-context-protocol)
  - [Claude Code and Computer Use](#claude-code-and-computer-use)
  - [Agents and Workflows](#agents-and-workflows)
  - [Putting It All Together](#putting-it-all-together)


## **12th October 2026**

Course: [Claude Academy – Anthropic](https://academy.claude.com/courses/ai-fluency-framework-foundations)

1. # **Introduction to AI Fluency**

AI Fluency is the ability to collaborate with AI effectively, efficiently, ethically, and safely.

The goal is not simply to write better prompts, but to develop the skills needed to work with AI as a capable partner while maintaining human judgment and responsibility.

## **Three ways to work with AI**

| Mode | Description | Example |
| :---- | :---- | :---- |
| Automation | AI performs a specific task following instructions. | Generate unit tests. |
| Augmentation | Humans and AI collaborate to improve results. | Discuss system architecture together. |
| Agency | AI operates more independently on your behalf within configured boundaries.	 | An AI agent handles a defined development workflow. |

2. # **The 4Ds Framework**

The framework introduces four essential competencies.

| Competency | Loop | Key question |
| :---- | :---- | :---- |
| Delegation | Outer loop | What should AI do, and what should I do? |
| Description | Inner loop | How should I communicate what I need? |
| Discernment | Inner loop | How do I evaluate AI's work? |
| Diligence | Outer loop | How do I use AI responsibly? |

The inner loop improves the work through instructions, evaluation, and feedback. The outer loop governs which work to delegate and who remains responsible for the result.

3. # **Delegation — Deciding What AI Should Do**

Delegation consists of three components.

## **Problem Awareness**

Understand the problem before deciding how AI should help.

Ask yourself:

* What am I trying to achieve?  
* What does success look like?  
* What tasks are required?  
* What decisions require human expertise?

## **Platform Awareness**

Understand the capabilities and limitations of AI tools.

Consider whether a tool can perform the task reliably, whether it has access to the necessary information, and whether another approach would be more appropriate.

## **Task Delegation**

Divide work strategically between humans and AI.

| Approach | When to use |
| :---- | :---- |
| Human only | High-stakes decisions, final approval, personal judgment |
| Human \+ AI | Brainstorming, planning, design, reviewing |
| AI with human review | Coding, documentation, test generation |
| AI automation | Repetitive, well-defined, low-risk tasks |

**Key lesson:** Effective delegation is not about automating everything. It is about finding the best division of work.

4. # **Description — Communicating Effectively With AI**

Description involves three types of communication.

| Component | Purpose | Example |
| :---- | :---- | :---- |
| Product Description | Describe the desired output. | Create a REST API specification. |
| Process Description | Explain how AI should approach the task. | Review requirements before writing code. |
| Performance Description | Specify how AI should behave. | Be concise, challenge assumptions, identify uncertainty. |

**Six effective prompting techniques**

* Provide context: Explain the background and goal.  
* Give examples: Show what a successful output looks like.  
* Set constraints: Specify technologies, format, scope, and limitations.  
* Break down complex tasks: Divide large requests into manageable steps.  
* Ask for analysis before a solution: Have AI examine requirements and alternatives first.  
* Define role and tone: Specify the expertise or communication style needed.

**Example prompt**

| Act as a senior backend engineer. Product: Design a REST API for managing motel rooms, tenants, invoices, and payments using FastAPI and PostgreSQL. Process: Start by identifying missing requirements, then propose the data model and endpoints. Explain important tradeoffs before implementation. Performance: Be concise, challenge weak assumptions, and follow production-ready practices. Do not invent business rules. |
| :---- |

**Key lesson:** A good prompt describes not only what you want, but also how AI should work with you.

5. # **Discernment — Evaluating AI's Work**

Discernment is the ability to critically evaluate AI-generated outputs, processes, and behavior.

**Three types of Discernment**

| Component | What to evaluate |
| :---- | :---- |
| Product Discernment | Is the output accurate, useful, complete, and appropriate? |
| Process Discernment | Did AI use a reasonable approach? Are there logical gaps or unsupported assumptions? |
| Performance Discernment | Did AI follow instructions and respond appropriately to feedback? |

**Example: Reviewing AI-generated code**

Suppose AI generates a FastAPI endpoint.

* Product evaluation:  
  * Does the endpoint satisfy the requirements?  
  * Does it handle errors correctly?  
  * Do the tests pass?  
* Process evaluation:  
  * Is the architecture appropriate?  
  * Are database transactions handled correctly?  
  * Are there security or concurrency concerns?  
* Performance evaluation:  
  * Did AI follow the project's coding conventions?  
  * Did it respect the specified technology stack?  
  * Did it explain important tradeoffs?

**Key lesson:** AI-generated work should be evaluated against the same quality standards as human-created work.

6. # **The Description–Discernment Loop**

AI collaboration is an iterative process rather than a single prompt and response: 

* **Describe** (Requirement) → **Generate** (AI output) → **Evaluate** (Human review)

**A practical workflow:**

* Describe the task and acceptance criteria.  
* Review the initial AI output.  
* Identify specific problems and gaps.  
* Provide targeted feedback.

* Repeat until the result meets expectations.

Avoid vague feedback like “Make it better.” Instead, clearly explain what the problem is, why it matters, and how it should be improved.

7. # **Diligence — Responsible AI Collaboration**

Diligence focuses on ethical, transparent, and responsible AI use.

**Three types of Diligence**

| Component | Responsibility |
| :---- | :---- |
| Creation Diligence | Choose appropriate tools and protect sensitive information. |
| Transparency Diligence | Be honest about how AI contributed. |
| Deployment Diligence | Verify and take responsibility for the final result. |

**Practical example: AI-assisted software development**

* **Creation:** Do not expose credentials, production secrets, or private customer data to AI services without appropriate safeguards.  
* **Transparency:** Clearly communicate AI assistance when required by your team or organization.  
* **Deployment:** Review generated code, execute tests, validate security, and confirm expected behavior before releasing it.

A **Diligence Statement** is a document that records which AI tools were used, how they contributed to the work, how humans reviewed and verified the output, and who takes responsibility for the final result.

**Key lesson:** Delegating work to AI does not transfer accountability away from the human responsible for the project.

# **AI Capabilities and Limitations**

## **13th October 2026**

Course: [Claude Academy – Anthropic](https://academy.claude.com/courses/ai-capabilities-and-limitations)

1. # **Introduction to AI Capabilities and Limitations**

Generative AI can produce impressive results, but it also has predictable limitations.

For example, AI can:

* Summarize a complex document in seconds.

* Generate code, articles, and creative ideas.

* Explain unfamiliar concepts.

* Follow detailed instructions and assist with problem-solving.

However, AI can also:

* Generate convincing but incorrect information.

* Invent facts, citations, or references.

* Forget important context.

* Misinterpret instructions.

* Make mistakes during complex reasoning.

**Key concept:** Understanding how AI works helps us predict when to trust its outputs, when to verify them, and how to improve results.

**The Four Properties of AI**

| Property | Main Question |
| :---- | :---- |
| Next Token Prediction | Where do AI answers come from? |
| Knowledge | What does AI actually know? |
| Working Memory | What information can AI consider right now? |
| Steerability | How effectively can we control AI through instructions? |

Each property exists on a continuum between capability and limitation.

2. # **What We Mean by AI**

Artificial Intelligence is a broad field that includes several types of systems.

## **Classification AI**

Classification AI identifies categories or patterns in data.

Examples:

* Detecting spam emails.

* Recognizing objects in images.

* Classifying customer reviews as positive or negative.

## **Prediction AI**

Prediction AI estimates future outcomes using historical patterns.

Examples:

* Predicting product demand.

* Forecasting sales.

* Estimating customer churn.

## **Generative AI**

Generative AI creates new content based on patterns learned during training.

Examples:

* Writing documents.

* Generating software code.

* Producing images.

* Summarizing information.

* Participating in conversations.

**Key takeaway:** Generative AI does not simply retrieve stored answers. It generates responses dynamically based on learned patterns, the current context, and available tools.

3. # **How AI Gets Its Character**

Large Language Models typically undergo two major training stages.

## **Pretraining**

During pretraining, a model learns patterns from large collections of data.

It develops capabilities involving:

* Language and grammar.

* General knowledge.

* Relationships between concepts.

* Coding patterns.

* Reasoning-related patterns.

The fundamental learning objective commonly involves predicting missing or subsequent tokens.

## **Fine-Tuning and Alignment**

After pretraining, additional training helps make the model more useful as an assistant.

This may involve:

* Learning to follow instructions.

* Improving response quality.

* Learning helpful conversational behavior.

* Reducing harmful or inappropriate outputs.

* Incorporating human or AI-generated feedback.

## **Behavioral Fingerprints**

Training can lead to recognizable behaviors.

| Behavior | Description |
| :---- | :---- |
| Sycophancy | Agreeing with the user too readily, even when the user is incorrect. |
| Verbosity | Producing unnecessarily long explanations. |
| Over-caution | Being excessively conservative or reluctant in some situations. |
| Poor confidence calibration | Expressing confidence that does not accurately reflect the likelihood of being correct. |

**Practical lesson:** A confident, friendly, and well-written answer is not necessarily a correct answer.

4. # **Next Token Prediction**

## **How It Works**

An LLM generates text by predicting one token at a time.

A token can represent a word, part of a word, punctuation, or another text unit.

The model evaluates possible next tokens using patterns learned during training and the current context.

For example:

* Input: "The capital of France is"  
* Likely continuation: "Paris"  
* The model continues predicting tokens until it completes its response.

## **Capabilities**

Next Token Prediction enables AI to:

* Produce fluent, natural language.

* Rewrite content in different styles.

* Summarize and transform information.

* Generate common programming patterns.

* Combine ideas across different topics.

## **Limitations**

Because generated text is not automatically verified against reality, the model may produce plausible but false information.

This is often called hallucination or fabrication.

Common examples include:

* Invented references or citations.

* Incorrect quotations.

* Nonexistent software methods.

* Fabricated statistics.

* False details about unfamiliar subjects.

## **How to Reduce Fabrication**

* Provide reliable reference material.

* Use web search for current information.

* Use retrieval systems for private or specialized documents.

* Require verification of important claims.

* Allow the model to acknowledge uncertainty.

* Use code execution or other tools when exact results are required.

**Key takeaway:** Fluency is not the same as factual accuracy.

5. # **Knowledge**

## **What Does AI Know?**

An LLM acquires much of its general knowledge through training.

Its knowledge is influenced by:

* The information included in training.

* How frequently subjects appear.

* The quality and consistency of sources.

* The model's knowledge cutoff.

## **Knowledge Strengths**

AI tends to perform better on:

* Widely documented topics.

* Common programming languages.

* Popular frameworks.

* Established concepts.

* Frequently discussed subjects.

## **Knowledge Limitations**

AI may be less reliable on:

* Recent events.

* Niche or obscure subjects.

* Rare languages or technologies.

* Private company information.

* Frequently changing APIs.

* Controversial or inconsistently documented topics.

## **Knowledge Cutoff**

A model's training knowledge generally does not automatically include events that occurred after its training cutoff.

For example, a model may explain how a software framework works but lack knowledge of a newly released version.

However, an AI system may overcome this limitation by using tools that retrieve current information.

## **Improving Knowledge Reliability**

| Problem | Recommended Solution |
| :---- | :---- |
| Outdated information | Web search or current documentation |
| Missing project details | Provide project files or relevant context |
| Private company knowledge | Connect authorized internal knowledge sources |
| Uncertain factual claims | Verify against reliable sources |
| Exact calculations | Use a calculator or code execution |

**Key takeaway:** A model's knowledge is not a complete or continuously updated database.

6. # **Working Memory**

## **What Is Working Memory?**

An AI model's working memory is primarily determined by its context window.

The context window is the amount of information the model can process within a particular interaction.

It may contain:

* System instructions.

* User messages.

* Conversation history.

* Uploaded documents.

* Tool outputs.

* Generated responses.

## **Context Window Limitations**

Context windows have finite capacities.

When a conversation becomes too large:

* Older information may be removed or summarized.

* Important instructions may no longer be available.

* The model may overlook relevant details.

* Response quality may decrease.

Even when content fits inside the context window, the model may not use every part of it equally effectively.

## **Context Is Not Long-Term Memory**

Context and persistent memory are different concepts.

Context window: Information available to the model during the current interaction.

Persistent memory: Information saved by an application or system and made available again in later interactions.

Starting a new conversation does not inherently preserve everything from a previous conversation.

Some AI products offer memory, projects, retrieval, or conversation-history features to help maintain continuity.

## **Strategies for Managing Context**

**Front-loading**

Place important instructions and requirements clearly near the beginning of a task.

**Chunking**

Divide large documents or tasks into smaller, manageable sections.

**Re-supplying critical information**

Repeat or provide important requirements again when needed.

**Summarization**

Maintain concise summaries of decisions, progress, and unresolved issues.

**External knowledge storage**

Store persistent project information in files, documentation, or a retrieval system.

**Practical Example: Software Development**

Instead of relying on one extremely long conversation:

1. Maintain a project requirements document.

2. Store architectural decisions separately.

3. Create coding conventions and guidelines.

4. Provide only the relevant files for each task.

5. Summarize completed work and important decisions.

**Key takeaway:** More context is not always better. Relevant, well-organized context is more valuable than large amounts of unrelated information.

7. # **Steerability**

## **What Is Steerability?**

Steerability describes how effectively an AI model can follow instructions and adapt its behavior to user requirements.

Users can influence:

* Response format.

* Tone and writing style.

* Level of detail.

* Role or perspective.

* Workflow.

* Output constraints.

## **Strong Steerability**

AI often follows concrete, verifiable instructions effectively.

Examples:

* "Respond using five bullet points."

* "Return valid JSON."

* "Explain this concept to a beginner."

* "Use Python instead of JavaScript."

* "Keep the summary under 150 words."

## **Weak Steerability**

AI may struggle with:

* Ambiguous requirements.

* Long or conflicting instructions.

* Complex chains of reasoning.

* Strict requirements involving exactness.

* Unstated intentions.

## **Common Failure Mode**

**Reasoning Drift**

Small errors accumulate during a complex, multi-step task and lead to an incorrect result.

**Letter-over-Spirit**

The AI follows the literal wording of an instruction but misses its intended purpose.

**Prompt Injection**

Untrusted content attempts to redirect the AI away from legitimate instructions.

## **Improving Steerability**

* Use clear, specific instructions.  
* Define acceptance criteria.  
* Provide examples.  
* Separate large tasks into smaller steps.  
* Clarify priorities when instructions conflict.  
* Review results and provide corrective feedback.

**Example**

* Weak instruction:  
  * "Build a good API."  
* Improved instruction:  
  * "Design a REST API using FastAPI and PostgreSQL. Include authentication, pagination, error handling, and unit tests. Follow REST conventions and explain important design tradeoffs."

**Key takeaway:** Precise instructions improve AI performance, but prompting alone cannot eliminate fundamental model limitations.

## **8\. When AI Properties Collide**

Real-world tasks usually involve multiple AI properties simultaneously.

Understanding their interactions helps identify why an output failed.

## **Example 1: Incorrect Research Summary**

Problem: AI summarizes a long technical document but invents supporting references.

Possible causes:

* Next Token Prediction: The model generates plausible citations.  
* Knowledge: It lacks reliable information about the subject.  
* Working Memory: Important details in the document are overlooked.

Solutions:

* Provide trustworthy source documents.  
* Process the document in smaller sections.  
* Require references to source passages.  
* Verify citations independently.

## **Example 2: Incorrect Generated Code**

Problem: AI generates code using methods that do not exist in the installed library version.

Possible causes:

* Knowledge: The model lacks current API information.  
* Next Token Prediction: It generates plausible-looking method names.  
* Steerability: The request did not specify the library version.

Solutions:

* Specify exact dependency versions.  
* Provide current API documentation.  
* Run tests and static analysis.  
* Ask AI to correct failures using actual error messages.

## **Example 3: Long Project Conversation**

Problem: AI begins contradicting earlier architectural decisions.

Possible causes:

* Working Memory: Previous decisions are no longer fully represented.  
* Steerability: Older instructions may have lost influence.  
* Next Token Prediction: The model generates a plausible alternative without respecting earlier decisions.

Solutions:

* Maintain a project specification.  
* Save important architectural decisions.  
* Reintroduce relevant constraints.  
* Divide work into smaller, focused tasks.

## **9\. Diagnosing AI Failures**

When AI generates an unexpected result, do not automatically repeat the same prompt.

Identify the underlying limitation first.

| Symptom | Likely Property | Targeted Fix |
| ----- | ----- | ----- |
| Invented facts or citations | Next Token Prediction | Verify using sources |
| Outdated information | Knowledge | Retrieve current information |
| Forgotten requirements | Working Memory | Reintroduce relevant context |
| Incorrect output format | Steerability | Clarify format and constraints |
| Mistakes in long reasoning | Steerability \+ Next Token Prediction | Break down and verify steps |
| Conflicting long-document summary | Working Memory \+ Knowledge | Chunk and ground in sources |
| Incorrect library API usage | Knowledge \+ Next Token Prediction | Supply documentation and run tests |

**Core principle:** Different failures require different solutions. Better prompting is only one possible intervention.

## **10\. Connecting AI Properties to the 4D Framework**

The course complements the AI Fluency Framework, which consists of Delegation, Description, Discernment, and Diligence.

| AI Property | Related Human Competency |
| ----- | ----- |
| Next Token Prediction | Discernment – evaluate generated content carefully |
| Knowledge | Delegation and Discernment – recognize when external information is needed |
| Working Memory | Description – organize and supply relevant context |
| Steerability | Description – communicate instructions clearly |
| All four properties | Diligence – ensure responsible use and human accountability |

These relationships are practical connections rather than exclusive one-to-one mappings.

## **Calibrated Trust**

Calibrated trust means adjusting how much confidence and autonomy we give AI depending on the task and its associated risks.

For example:

**Higher trust, lighter review**

* Reformatting text.  
* Brainstorming ideas.  
* Generating first drafts.

**Moderate trust, structured verification**

* Generating code.  
* Summarizing technical documents.  
* Comparing architectural approaches.

**Lower trust, rigorous verification**

* Financial decisions.  
* Legal or medical information.  
* Security-sensitive software.  
* Critical production deployments.

Trust should depend on the task, the evidence, the available tools, and the potential consequences of errors.

# **The AI-native SDLC Playbook**

## **27th October 2026**

Course: [Claude Academy – Anthropic](https://academy.claude.com/courses/ai-native-sdlc-playbook)

1. # **Introduction: Why the SDLC Has to Change**

AI agents now write code much faster than before, but the process around the code (approval gates, reviews, handoffs, policies) still runs at human speed. That process stalls the productivity gained from tools like Claude Code.

The traditional SDLC was designed for a time when writing code was the slowest and most expensive stage. PRDs, estimation rituals and security reviews existed to force alignment before weeks or months of coding.

## **When code is no longer the bottleneck**

* The bottleneck moves to the stages around Build: planning, review/testing and deployment, which still run at human speed.  
* Controls stop matching reality. Reviewing every line by hand worked when a person wrote it, not when agents write most of the diff.  
* Governance costs rise, because exceptions still go through weekly or monthly committees.

**Example:** Security teams are sized for human output. When agents multiply code output, either the review queue grows or code ships under-reviewed. A regulated company can accept neither.

## **Traditional vs AI-native SDLC**

The AI-native SDLC keeps the old control objectives but enforces them in new ways. The linear flow becomes a loop, with AI embedded at every stage and humans above the loop instigating, directing and governing.

| Stage | Traditional SDLC | AI-native SDLC |
| :---- | :---- | :---- |
| Plan | Requirements gathered by committee, workshops and sign-offs, written by hand. | Claude synthesizes pain points from the sources and captures them in intent.md. |
| Design | Spec written by analysts, then parsed by designers. | Requirements and design done in one session with an agent, guided by standards encoded as skills. |
| Build | Code and tests handwritten; docs written afterwards. | Code and tests generated by AI; knowledge kept in versioned CLAUDE.md files and skills. |
| Test | QA gates at stage boundaries. | Continuous evals woven through implementation. |
| Deploy | Humans review every line; governance happens in review cycles. | Layers of agentic review; human review for regulated or critical code; hooks as approval gates. |
| Maintain | Humans watch production for bugs. | Agents monitor deployments; a breached control band becomes a new intent.md. |

## **The committed artifact chain**

Each stage ends by committing an artifact to version control, and the next stage starts by reading it. The chain of commits is also the audit trail: who asked for what, what the agent produced, and who approved it.

| Artifact | Produced in | Triggers |
| :---- | :---- | :---- |
| intent.md (accepted) | Plan | Requirements and design pass |
| spec.md (approved) | Design | Plan mode |
| plan.md \+ diff \+ tests | Build / Test | PR and review |
| Merged PR | Deploy | CI/CD pipeline |
| Breached control band | Maintain | A new intent.md |

## **How each play is structured**

The course has 12 plays grouped into 6 stages. Plays are modular, so a team can adopt them in any order that their prerequisites allow. Each play covers:

* What changes (traditional vs AI-native).  
* Getting started: prerequisites and infrastructure.  
* Steps to execute it.  
* Governance considerations.  
* How to measure it: a leading and a lagging indicator.

**Key lesson:** At first each step is prompted by hand. The end state is a loop where each accepted artifact fires the next gate, and human attention concentrates at the gates. Humans stay accountable for every decision that needs judgment.

2. # **Stage 1 Plan: Capture as intent.md**

intent.md is a short, version-controlled proto-spec that states what is wanted, why, and under which constraints. It can start from a person's idea, a ticket, or a production alert (Stage 6).

Instead of passing an idea through backlog entries, user stories, story points and refinement meetings, the originator brainstorms with Claude and writes it down in their own words.

## **Steps**

* The originator describes the problem to Claude in plain words: what is not possible today, who is affected, what better looks like, what is out of scope.  
* Brainstorm until the idea is concrete. Claude asks the questions an analyst would ask: scope, users, constraints, success criteria.  
* Claude writes intent.md using the organization's template (the template can be a skill).  
* The originator corrects anything Claude misunderstood.  
* Commit intent.md to the shared intent home, usually an intent/ folder in the product repo. Non-engineers can commit through a GitHub connector from claude.ai.

## **intent.md template**

A typical intent.md has these sections:

| Section | Content |
| :---- | :---- |
| Header | Title, author, status (draft / accepted) |
| Problem | What hurts today and for whom |
| Proposed outcome | What success looks like |
| Affected users and systems | Teams, services and APIs involved |
| Constraints | Security, data, auth or technical limits |
| Open questions | What still needs a decision |

## **Governance and metrics**

* **Governance:** Git records author, timestamp and revisions. The product owner accepts (merge) or rejects (close) the intent.  
* **Leading indicator:** Time from first conversation to committed intent.md, expected to fall from weeks to hours.  
* **Lagging indicator:** Survival rate, the share of intent.md files accepted into Design.

3. # **Stage 2 Design: Requirements and Design**

After the product owner accepts intent.md, Claude produces a requirements and design spec (spec.md) in one session. The spec is constrained by the organization's skills for brand, security, compliance and UX, and it flags areas of concern. The product owner reviews the spec but does not write it.

For front-end work, the product owner can mock the design in Claude Design from intent.md, iterate on it, and export it to Claude Code to build.

## **Steps**

* Open a session with the organization's skills loaded and attach intent.md.  
* Prompt Claude to produce spec.md, apply the skills, and clearly flag concerns, especially conflicting policies.  
* Review the spec against the idea: does it solve the stated problem, and are the open questions answered or carried forward?  
* Resolve flagged concerns first, each with its policy owner, before engineering sees the spec.  
* Commit spec.md next to intent.md. The pair records what was asked and what was decided.  
* A human decides whether to proceed to Build. Accepting the spec starts the plan mode play.

**Automation path:** Run the pass by hand first, then turn it into an organization slash command, and finally a CI job that runs when intent.md is merged and opens spec.md as a PR.

## **Governance and metrics**

* **Governance:** Live policy is applied while the spec is written, instead of being discovered in a review weeks later. The spec, the prompt and the skill versions are all in version control.  
* **Leading indicator:** Time between the intent.md commit and the spec.md commit.  
* **Lagging indicator:** Requirements rework, counted as spec.md commits after the first plan.md commit.

4. # **Stage 3 Build: Plan Mode as the Default Starting Point**

Engineers start Claude Code sessions in plan mode, where Claude can read the codebase without changing anything. They give it the approved spec.md, let it interview them, and iterate on the plan before any code is written.

## **Steps**

* Start the session in plan mode.  
* Give Claude intent.md and spec.md and ask for an implementation plan: files that change, order of work, tests that prove it.  
* Challenge the plan: what could it break, which step is riskiest, which alternatives were rejected?  
* Iterate until an engineer who never saw the conversation could implement it from the plan alone.  
* Commit the approved plan as plan.md. PR review later checks the diff against it.  
* Accept the plan and let Claude implement. With a solid plan this is often a single pass.  
* If the implementation departs from the plan, update plan.md in the same commit (a hook can enforce this).

**plan.md contains:** files that change, order of work, risks, and proof (tests, screenshots).

## **Auto mode**

In auto mode the engineer approves the plan and Claude applies each change without a per-edit prompt. As guardrails mature (tuned CLAUDE.md, skills, hooks, a runnable test suite), auto mode becomes the default for routine work. Review shifts from watching each edit to reviewing artifacts after longer autonomous sessions, and it enables parallel work with worktrees.

## **Legacy systems and the source of truth**

Existing tools (Jira, requirements tools, Figma, change boards) are hard to replace because auditors and other teams rely on them. For each artifact, name one system as the source of truth:

| Option | How it works |
| :---- | :---- |
| Repo as source of truth | Markdown artifacts are authoritative; the legacy system links to commits. Cleanest for engineering-led teams. |
| Legacy system as source of truth | Jira/ServiceNow holds the record; Claude reads it at session start and writes back via an MCP connector. |
| Linkage (minimum bar) | Artifacts note the record ID, records note the commit SHA. A good starting point during transition. |

## **Governance and metrics**

* **Governance:** Design review happens before code exists, when changing course means editing a document. Higher-risk plans go to a tech lead or architect.  
* **Leading indicator:** Share of changes merged from the first implementation pass; time from plan approval to merged PR.  
* **Lagging indicator:** Rework cycles per change and how often the merged diff still matches plan.md.

5. # **Stage 3 Build: The CLAUDE.md**

CLAUDE.md gives Claude the context a new joiner would need: conventions, commands, architecture and the mistakes the team sees most often. Claude reads it at the start of every session, and the whole team maintains it.

## **Steps**

* Run /init in the repo to generate a starting CLAUDE.md.  
* Cut it down to what a new joiner needs on day one: build, test and lint commands, important conventions, things Claude keeps getting wrong.  
* Commit it at the repo root so the team shares one reviewed version.  
* Working rule: when Claude makes the same mistake twice, the correction goes into CLAUDE.md.  
* Keep it under one page. Claude reads all of it, so stale content wastes context.

**Typical sections:** Commands, Conventions, Architecture, Things Claude gets wrong.

## **Governance and metrics**

* **Governance:** The file is version controlled, so the agent's instructions are reviewable; code owners approve changes in PR review.  
* **Leading indicator:** How often Claude repeats a mistake CLAUDE.md should have caught.  
* **Lagging indicator:** Time to first merged PR for a new team member.

6. # **Stage 3 Build: Skills as Institutional Knowledge**

Skills turn institutional knowledge into explicit, version-controlled instructions that are applied consistently and updated centrally when policy changes. Write a skill for knowledge that must be applied consistently; put general project context in CLAUDE.md or a prompt instead.

## **Steps**

* Pick one piece of knowledge that is enforced inconsistently today, such as a security standard, an API convention or a brand rule.  
* Write it as a skill: a folder with a SKILL.md whose frontmatter says when it triggers and whose body says what to do.  
* Store it in .claude/skills/\<name\>/ in the repo, or distribute it organization-wide as a plugin.  
* Test that it triggers by asking for the relevant task in different ways.  
* When the policy changes, update the skill and have the policy owner sign off. Engineers get the new version in their next session.

## **Skills vs hooks**

A skill is advisory: it makes Claude likely to follow a policy, but nothing forces it. A policy that must always hold needs a deterministic control behind it.

|  | Skill | Hook |
| :---- | :---- | :---- |
| Type of control | Advisory | Deterministic |
| Effect | Makes violations rare | Makes violations close to impossible |
| Build-time examples | Secure API review checklist | Block edits to protected paths, run formatter/linter after edits, keep credentials out of the diff |

Build-phase hooks run on every matching action, so keep them fast and scoped to the changed file. Heavy checks (full test suite) belong at commit or PR, and hooks that ask a human for approval belong at the Deploy gates.

## **Governance and metrics**

* **Governance:** Skill invocations are logged in session traces; the policy owner reviews skill changes like code.  
* **Leading indicator:** Time from a policy change being approved to the updated skill merging.  
* **Lagging indicator:** PR review findings that cite the policy, which should fall toward zero.

7. # **Stage 3 Build: Parallel Sessions and Subagents**

One engineer can drive several streams of work at once. The engineer's job shifts from writing code to steering and reviewing, and eventually to building and monitoring loops.

|  | Parallel session | Subagent |
| :---- | :---- | :---- |
| What it is | A full Claude Code instance on a separate task in its own Git worktree | A scoped helper inside one session with its own context window and tool limits |
| Purpose | More tasks in flight per engineer | Keeps each session focused; handles recurring jobs |
| Example | claude \--worktree feature-auth | verifier, code simplifier, researcher |

## **Steps**

* Use plan.md to split work into tasks that touch different files. Tasks sharing files run one after another in a single session.  
* Give each parallel task its own worktree so sessions do not collide on files.  
* Start with 2 or 3 sessions. The limit is how many streams one person can review properly.  
* Define recurring jobs as subagents in .claude/agents/ (name, when to use it, allowed tools) and commit them to Git.

## **Governance and metrics**

* **Governance:** Hooks and permission settings in the repo apply to all sessions; each session's actions are attributed to the engineer who ran it.  
* **Leading indicator:** Concurrent sessions per engineer while review quality holds.  
* **Lagging indicator:** Changes merged per engineer per week, read alongside the rework rate.

8. # **Stage 4 Test: Give Claude a Feedback Loop**

Always give Claude a way to verify its own work: tests, a build, or a screenshot diff. Claude iterates until the check passes, so what reaches the engineer has already passed it.

The feedback loop runs throughout the task. A verifier subagent is different: it is a final check in a fresh context once the session thinks the work is done.

## **Steps**

* Wrap verification in single commands (make test, npm test) that exit non-zero on failure.  
* List each command in the CLAUDE.md Commands section with an example of healthy output.  
* Give a measurable target, for example all tests in a file pass or the screenshot matches the mock.  
* For bug fixes, write the failing test first, confirm it fails for the expected reason, commit it, then ask Claude to make it pass without editing the test.  
* For UI work, give Claude a browser or screenshot tool and the mock: implement, screenshot, compare, adjust (2 or 3 rounds is normal).  
* Make verification part of done: run the tests before reporting complete and show the output.  
* Protect the loop: a hook blocks edits to test files during a fix task.

## **Governance and metrics**

* **Evidence:** The literal test output, build log or screenshot diff, logged in the session transcript and the PR check run.  
* **Leading indicator:** First-pass CI success rate for agent-written changes.  
* **Lagging indicator:** Review time per PR and change failure rate.

9. # **Stage 4 Test: Continuous Evals in CI**

Evals are the AI-native version of stage-gate QA. An eval suite runs whenever the agent's configuration changes (new model, rewritten prompt, changed skill) and shows whether the agent still works to the same standard. The suite is live: add new cases as old ones stop discriminating.

## **Steps**

* Collect 20 to 50 real tasks from recent work, each with its expected or accepted outcome.  
* Write each task as an eval: the prompt plus checks that define acceptable (tests pass, lint clean, behavior unchanged, policy followed).  
* Run the suite non-interactively in CI on a schedule and on any change to CLAUDE.md, skills or hooks.  
* Gate configuration changes on the results: a change that drops the pass rate is reviewed before merging.  
* Every production incident becomes a permanent regression eval.

## **Governance and metrics**

* **Governance:** The pass-rate threshold is a merge check; runs are logged so results can be compared over time.  
* **Leading indicator:** Eval pass rate over time and how quickly an incident becomes an eval.  
* **Lagging indicator:** Regressions caught in CI vs regressions found in production.

10. # **Stage 5 Deploy: AI in the PR Review Loop**

Claude both reviews incoming PRs against the organization's policies and addresses review comments on its own PRs. Every PR gets the same review passes with findings ranked by severity, so engineers can focus on intent and risk.

## **Steps**

* Enable the managed Code Review service (fastest start) or run claude-code-action in your own CI for more control.  
* The tech lead writes REVIEW.md at the repo root: the review passes, what counts as Important vs Nit, and what to skip.  
* Findings never approve or block a PR on their own. Branch protection still requires a code owner's approval.  
* Tag @claude on a review comment and Claude fixes it and pushes. For Claude's own PRs, a slash command can sweep comments and failing checks until the PR only waits on approval.  
* Feed findings back: when a review flags the same mistake twice, add the fix to CLAUDE.md.  
* Tune monthly: rate findings, cap nits, exclude generated paths and anything CI already checks.

Typical review passes in REVIEW.md:

| Pass | Looks for |
| :---- | :---- |
| Bugs | Logic errors, broken edge cases, subtle regressions |
| Security | Injection risks, authentication gaps, PII in logs |
| Compliance | Change matches spec.md, plan.md and design principles |

## **Governance and metrics**

* **Governance:** Separation of duties is preserved: the agent that wrote the code cannot approve it. The PR history is the audit record.  
* **Leading indicator:** Time to first review (minutes) and share of comments resolved without a human touching the branch.  
* **Lagging indicator:** Defects caught before merge vs defects escaping to production.

11. # **Stage 5 Deploy: Hooks as Approval Gates**

In Build, hooks allow or block actions automatically. A hook can also ask, pausing the action until a specific person approves, which is what release gating needs. Hooks run wherever Claude acts, not only at deploy.

## **Steps**

* Leadership, change management and compliance list the human approval gates that must survive, such as change sign-off, release authorization and edits to protected paths.  
* The platform engineer expresses each gate as a hook: a script that runs before Claude acts and can allow, ask or block.  
* Team hooks go in .claude/settings.json in Git; non-negotiable hooks go in managed settings that engineers cannot turn off.  
* A block should explain itself: show the reason and the route to approval in Claude's output.

**Example:** A PreToolUse hook on Bash checks whether a command deploys to production without a release approval and blocks it (exit code 2 blocks the action and sends the message to Claude).

## **Managed settings for a regulated enterprise**

Managed settings are deployed by the platform team (MDM or admin console) and cannot be overridden by engineers. Key controls:

| Setting | What it controls |
| :---- | :---- |
| permissions.deny / allow | Keep secrets and network tools out; pre-approve the safe inner loop (git, build, test, lint) |
| disableBypassPermissionsMode, allowManagedPermissionRulesOnly | Nobody can widen the rules |
| sandbox | OS-level filesystem and network isolation, domain allowlist, deny credential files |
| allowManagedHooksOnly | Only hooks from managed settings run |
| disableSideloadFlags, strictKnownMarketplaces | Skills, agents and plugins only from the approved marketplace |
| allowManagedMcpServersOnly | The agent's tool surface is an allowlist |
| requiredMinimumVersion | Refuse to start on an unassessed version |

## **Governance and metrics**

* **Governance:** The gate is enforced every time, for everyone; allow and block decisions are logged with timestamps.  
* **Leading indicator:** Time spent waiting on each approval gate (from the OpenTelemetry export).  
* **Lagging indicator:** Gate violations reaching production before and after hooks.

12. # **Stage 5 Deploy: CI/CD Integration and Deployment**

Run Claude Code non-interactively inside the pipeline for steps that need judgment (triaging a broken build, a flaky test, writing the changelog). Sandbox the execution, expose deployment through MCP, and rehearse rollback before the agent needs it.

## **Steps**

* Start with read-only steps: claude \-p in a pipeline job to triage a failed build or draft the changelog.  
* Add write steps behind existing gates (fix lint, update docs, address @claude comments). Everything arrives as a PR; the agent cannot push to main.  
* Sandbox agent jobs: containers, network policy, short-lived scoped tokens, no production credentials by default.  
* Expose deploy, status and rollback as MCP tools scoped per environment.  
* Tier autonomy by environment (see table).  
* Make rollback the most rehearsed path: one command the agent can run, exercised regularly in staging.

Autonomy by environment:

| Environment | Agent autonomy |
| :---- | :---- |
| Development | Agent deploys freely |
| Staging | In between |
| Production | Agent prepares the release; a release manager authorizes it; a hook enforces the gate |

**Key principle:** The agent may act up to the production gate and cannot pass it.

## **Metrics**

* **Leading indicator:** Share of pipeline failures triaged without paging a human.  
* **Lagging indicator:** DORA metrics from the CI system and deployment tooling.

13. # **Stage 6 Maintain: Closing the Loop on Metrics**

Every earlier stage needs a person to start it. In Stage 6, a trigger (a control-band breach, a ticket, a channel message or a schedule) invokes Claude with no person in the path. Claude diagnoses, acts only through gated routes, and writes what it finds as a new intent.md, which restarts the loop. People triage and review instead of starting the work.

## **Steps**

* Pick one metric with a stable rolling baseline: CI test failure rate, post-deploy 5xx rate or PR cycle time.  
* Write a deterministic, unit-tested detection script (rolling mean and standard deviation with Western Electric rules) that catches both slow drift and spikes. No model is involved in detection.  
* Define response tiers in version-controlled config (bands.yaml).  
* Trigger via a scheduled workflow, a monitoring webhook or a cron job. Claude runs stateless in CI or as an Agent SDK service in a sandbox.  
* The agent writes its diagnosis as intent.md: anomaly and evidence, proposed outcome, affected systems, open questions.  
* The service owner triages: fix now, schedule or dismiss. Dismissals tune the bands.  
* When a fix ships, add an eval for the incident.

Response tiers:

| Band | Action |
| :---- | :---- |
| 1σ | Log only |
| 2σ | Claude diagnoses, read-only |
| 3σ | Claude may act: open a PR into the review gate or trigger a pre-approved runbook such as rollback |

## **Claude on call with Claude Tag**

Incidents also arrive through Slack or Teams. Claude Tag makes Claude a member of incident channels, so each incident gets a first responder. Anyone in the channel can guide the response, Claude verifies the metric is back at baseline through MCP, and writes the post-mortem to a version-controlled lessons file. Small fixes arrive as PRs; larger work becomes an intent.md.

## **Governance and metrics**

* **Governance:** Tier boundaries are enforced from config; managed settings deny production access; runbooks are approved in advance.  
* **Leading indicator:** Time from band breach to an intent.md in the triage queue.  
* **Lagging indicator:** Share of findings that become merged fixes, and repeat incidents of the same class.

14. # **Closing: Play Dependencies and Resources**

Models and harnesses can now transform the whole SDLC, not only code production, while keeping human judgment central and meeting enterprise governance needs. Plays without prerequisites are good places to start.

| Play | Needs first |
| :---- | :---- |
| Capture intent, CLAUDE.md, Skills, Feedback loop, Hooks, Plan mode | Nothing |
| Subagents | CLAUDE.md (feedback loop helps) |
| Evals | CLAUDE.md and feedback loop |
| Requirements and design | Capture intent and Skills |
| PR review | Evals and Subagents (Skills help) |
| CI/CD | PR review and Hooks |
| Closing the loop | CI/CD and Capture intent |

**Platform setup docs (rollout order):** admin setup, settings and managed settings, permissions, sandboxing, hooks, skills, plugin marketplaces, managed MCP, enterprise deployment (Bedrock, Vertex AI, Foundry), network config, monitoring (OpenTelemetry), Compliance API, security model.

**Key takeaway:** Speed up the process around the code, not just the code. Each stage commits an artifact that triggers the next, gates enforce governance as the AI acts, and humans focus on judgment at the gates.

15. # **Putting It All Together: The End-to-End Loop**

The 12 plays are not separate tools. They form one loop: each stage reads the artifact the previous stage committed, Claude does the work, and a human approves at a gate before the next stage starts. The loop then feeds itself, because production issues come back in as new intents.

## **The full loop at a glance**

Each row is one step of the loop, in order:

| Stage | Claude does | Committed output | Human gate |
| :---- | :---- | :---- | :---- |
| Plan | Brainstorms the idea, ticket or alert and writes the proto-spec | intent.md | Product owner accepts or rejects |
| Design | Writes requirements and design with the org skills loaded, flags concerns | spec.md | Product owner signs off; policy owners resolve concerns |
| Build | Plans in plan mode, then implements in parallel worktrees with subagents | plan.md, code and tests | Engineer approves the plan |
| Test | Runs tests, build and screenshots until they pass; **evals** check the agent's configuration | Passing **checks**, **eval** results | Pass-rate threshold as a merge check |
| Deploy | Reviews against REVIEW.md, fixes comments, prepares the release in CI/CD | Reviewed PR, release | Code owner approves; release manager authorizes production |
| Maintain | Diagnoses control-band breaches and incidents | A new intent.md | Service owner triages |

## **What supports every stage**

Three building blocks run underneath the whole loop:

* **CLAUDE.md:** shared project context that every session reads, updated whenever Claude repeats a mistake.  
* **Skills:** policies (security, brand, API, compliance) applied while the work is done, from Design through Review.  
* **Hooks and managed settings:** deterministic controls that block unsafe actions and enforce approval gates wherever Claude acts.

## **Example: one change through the loop**

A claims team wants customers to see their claim status in the portal:

* **Plan:** A claims handler describes the problem to Claude, which writes intent.md. The product owner accepts it.  
* **Design:** Claude produces spec.md with the security and UX skills loaded, and flags that no new PII may enter the portal session.  
* **Build:** An engineer runs plan mode, commits plan.md, and lets Claude build the API endpoint and the UI panel in two worktrees.  
* **Test:** Claude runs the tests and compares the panel screenshot with the mock until both pass.  
* **Deploy:** The AI review checks the PR against spec.md and plan.md, a code owner approves, and the release manager authorizes production.  
* **Maintain:** A monitoring script sees the status API error rate break its 3σ band. Claude diagnoses it and writes a new intent.md, and the loop starts again.

## **How each role's work changes**

* **Product owners** review intent.md and spec.md instead of writing requirements by hand.  
* **Engineers** steer several sessions and review plans and diffs instead of writing every line.  
* **Tech leads and policy owners** maintain CLAUDE.md, REVIEW.md and skills instead of repeating the same feedback.  
* **Platform teams** own the hooks, managed settings, evals and pipelines that connect the stages.

## **Suggested adoption path**

Start with the plays that have no prerequisites, then build up:

* **Foundations:** CLAUDE.md, plan mode, the feedback loop and intent.md.  
* **Policies and controls:** skills and hooks.  
* **Scale:** parallel sessions, subagents and evals.  
* **Automation:** AI PR review, then CI/CD integration.  
* **Autonomy:** closing the loop on metrics, so production issues restart the cycle on their own.

**Key takeaway:** The AI-native SDLC is one loop held together by committed artifacts: intent.md, spec.md, plan.md, the PR and the incident record. Claude does the work at each stage, controls are enforced as it acts, and humans spend their time at the gates making the judgment calls.

# **Claude Code in Action**

## **27th October 2026**

Course: [Claude Academy – Anthropic](https://academy.claude.com/courses/claude-code-in-action)

1. # **Introduction: From Single Prompts to Hands-Off Sessions**

The course is for developers who already use Claude Code for single prompts and want to run longer, less supervised sessions that the whole team can trust. It assumes basic Git and command-line skills.

It is organized around four skills:

| Skill | What it covers |
| :---- | :---- |
| Steer the work | Plan mode, compaction, rewind, goals, loops and worktrees |
| Configure Claude | CLAUDE.md, skills, permission modes and hooks |
| Automate repeat work | Routines, headless mode, the Agent SDK, Code Review and the GitHub Action |
| Verify and share | Checking unsupervised runs and packaging a setup as a plugin |

2. # **Steering Long Sessions**

Long tasks such as multi-file refactors or new features can run for hours. Two habits keep them on track: scope the work before Claude starts, and steer it while it runs.

## **Scope first with plan mode**

* In plan mode Claude researches read-only, reads the code and proposes a plan for you to review.  
* Read the plan carefully and ask Claude to revise anything wrong or missing. Fixing a plan is faster than cleaning up after a bad run.

## **Steer while Claude works**

* **Compact:** /compact summarizes the conversation to free up context. Add a focus, for example /compact Focus on the \--version flag implementation, so the summary keeps what matters.  
* **Rewind:** every prompt is a checkpoint. Double-tap Escape on an empty prompt to open the rewind menu.

Rewind menu options:

| Option | Effect |
| :---- | :---- |
| Restore code and conversation | Rolls back files and chat |
| Restore conversation | Rolls back the chat only |
| Restore code | Rolls back the files only |
| Summarize from here | Compresses everything after the checkpoint, useful after a side conversation |
| Summarize up to here | Compresses everything before the checkpoint, useful after a long setup phase |

## **Let Claude run more autonomously**

* **Goal:** /goal sets a completion condition, for example all tests in src/billing pass and the type checker reports zero errors. Claude keeps working until an evaluator confirms it, and /goal clear cancels it. The condition must be checkable from Claude's visible output.  
* **Loop:** /loop reruns a prompt on a fixed or self-paced interval, useful for watching a CI run or a deployment. Escape stops it.  
* **Worktrees:** each parallel session gets its own file tree, so agents cannot overwrite each other. A .worktreeinclude file at the repo root lists git-ignored files (such as local env files) to copy into each worktree.

**Key lesson:** Scope first, then steer. Use a goal when describing done is easier than describing the steps.

3. # **A CLAUDE.md That Gets Followed**

CLAUDE.md is guidance, not enforced configuration. Every line competes for Claude's attention, so the leaner the file, the more of it Claude follows.

## **Pick the right tool**

CLAUDE.md is for soft conventions and preferences. Hard rules such as never pushing to main belong in a PreToolUse hook, which blocks the action even if Claude tries it.

## **The four CLAUDE.md locations**

Claude loads all four at launch, and they stack:

| Location | Scope | Notes |
| :---- | :---- | :---- |
| Managed policy | Whole organization | Set by the platform team; cannot be excluded |
| User | You, across all projects | Lives on your machine |
| Project | The team | Checked into the repo |
| Local | You, this repo only | Git-ignored; good for personal notes on a branch |

## **Writing rules that stick**

* **Imports:** split a long file with lines like @.claude/conventions/testing.md. This organizes the file but does not reduce context, since everything still loads at launch.  
* **Be specific and checkable:** write “Put new API routes in src/api/handlers, one per file” instead of “follow best practices”.  
* **Name the replacement:** write “Use named exports, not default exports” instead of only banning default exports.  
* **Treat emphasis as a budget:** keep IMPORTANT or YOU MUST for the two or three rules where a violation hurts most.  
* **Keep it under revision:** treat each mistake as a bug report against CLAUDE.md and ask Claude to add the rule.

**Key lesson:** Treat CLAUDE.md like production code. If a line cannot be justified, delete it.

4. # **Verification Skills**

Verification is the first skill to build. Without it, checking Claude's work depends on someone remembering to ask. A verification skill fires automatically when a finished task matches its description and runs the same checks every time.

## **What the skill does**

* Runs the test suite.  
* Reads the diff and checks that no test was weakened to make it pass.  
* Reports pass or fail with the evidence attached.

Done means the gates were run, the results were observed and they were reported, not that the diff looks right. Rule of thumb: if you have typed the same multi-step instruction twice, make it a skill.

## **Skill structure**

* **skill.md:** the name, the trigger description and the procedure. Keep it lean.  
* **reference.md:** detailed material Claude reads only when it needs it.  
* **Scripts (for example check.sh):** Claude runs them instead of loading them into context, so a skill can carry its own tooling.  
* Only skill descriptions load into context until a skill is needed, so many skills cost little. Commit them to .claude/skills so the team shares them.

## **Which surface owns which rule**

Each kind of rule has a home:

| Surface | Use it for | Example |
| :---- | :---- | :---- |
| CLAUDE.md | Conventions that always apply | Naming rules, where files go |
| Skill | Procedures for a type of task | Verification flow, release checklist |
| Hook | Rules Claude must not skip | Enforced checks |

**Key lesson:** CLAUDE.md and skills are instructions Claude follows; a hook is code that runs. Non-negotiable rules need a hook.

5. # **Permission Modes**

A permission mode sets which actions Claude can take without asking. Deny rules still apply in every mode.

| Mode | Runs without asking | Best for |
| :---- | :---- | :---- |
| default (Manual) | Reads only | Sensitive work, reviewing every action |
| acceptEdits | Reads, file edits and common file commands in the working directory | Iterating on code you are reviewing |
| plan | Reads only; edits are blocked until you approve a plan | Exploring before changing anything |
| auto | Everything, with a classifier reviewing each action | Long tasks with fewer prompts |
| dontAsk | Reads and pre-approved tools; anything else is denied | Locked-down CI and scripts |
| bypassPermissions | Everything | Isolated containers and VMs only |

## **Switching modes**

* Press Shift+Tab during a session to cycle through modes.  
* Start in a mode with claude \--permission-mode plan.  
* Set a default with permissions.defaultMode in settings.json.  
* For headless runs, pass the mode explicitly, for example claude \-p "..." \--permission-mode dontAsk.

## **Auto mode vs bypass**

* **Auto mode:** a separate classifier blocks actions that go beyond the request, touch unknown infrastructure or look driven by hostile content, such as force pushes, production deploys or curl \| bash. After 3 blocks in a row or 20 in total it falls back to prompting.  
* **bypassPermissions:** no checks at all and no protection against prompt injection. Use it only in sandboxes without internet access; admins can disable it.  
* **Limit:** the classifier judges danger, not correctness, so the work still needs verifying.

6. # **Hooks**

A CLAUDE.md rule is a request; a hook is deterministic code that runs at a fixed point in the agent loop. Use hooks for anything that must happen every time, including on unattended runs.

## **Main hook events**

Claude Code fires around 30 events; these matter most:

| Event | Fires | Typical use |
| :---- | :---- | :---- |
| PreToolUse | Before a tool call | Block, allow, ask or rewrite the call |
| PostToolUse | After a successful tool call | Format, lint, type check |
| Stop / SubagentStop | When Claude or a subagent tries to finish | Refuse to stop until tests pass |
| SessionStart | At session start, and after compaction with the compact matcher | Set up the environment, restore context |
| PreCompact / PostCompact | Around compaction | Compaction handling |
| InstructionsLoaded | When a CLAUDE.md or rule file loads | Audit what entered context |

## **Controlling the outcome**

* **PreToolUse JSON:** return permissionDecision as allow, deny or ask (defer only for \-p runs). updatedInput rewrites the call but replaces the whole input, so echo back the fields you are not changing.  
* **Exit 0:** success, and JSON on stdout is parsed. Plain text is added to context only on SessionStart, UserPromptSubmit and UserPromptExpansion.  
* **Exit 2:** blocks the action and sends stderr back to Claude. On Stop it tells Claude it is not finished.  
* **Any other code, including exit 1:** logged only, nothing is blocked. This is a common mistake.  
* **Config:** a matcher picks the tool (for example Bash), and an optional if clause narrows it to specific commands.

## **Examples**

* **Redact instead of block:** a PreToolUse hook spots an sk\_live\_ secret in a Bash command and replaces it with a placeholder through updatedInput, so the task still completes.  
* **Keep state after compaction:** a SessionStart hook with the compact matcher prints a short list of recently edited files, so Claude does not resume cold.

**Key lesson:** Use exit 2 to block. PostToolUse runs after the tool, so it can give feedback but cannot prevent the call.

7. # **Routines and Headless Mode**

Once Claude handles a task reliably by hand, stop running it by hand. The options range from fully managed (routines) to fully custom (the Agent SDK).

## **Routines**

* A routine is a saved prompt plus a repo and any connectors, run on Anthropic's infrastructure with nothing to host.  
* Triggers: a cron schedule, an HTTP POST to its API endpoint, or a GitHub event such as a new PR.  
* Create one at claude.ai/code/routines or with /schedule, for example /schedule daily dependency audit at 9am.  
* Limits: research preview, at most once per hour, and each run starts from a fresh clone and can only push to claude/ branches by default.

## **Headless mode and the Agent SDK**

* claude \-p runs once with no UI and composes with shell tools through stdin and stdout.  
* \-p skips auto-discovery of CLAUDE.md, hooks, skills, plugins and MCP servers, so pass what you need explicitly. In return, startup is much faster.  
* **Structured output:** \--output-format json with \--json-schema puts the result in structured\_output, ready for jq.  
* **Multi-step runs:** save session\_id from the JSON output and continue later with claude \--resume.  
* **CI:** add \--bare for repeatable runs.  
* **Agent SDK:** the same engine as a TypeScript or Python library (query function, allowedTools, system prompt, permission mode) for embedding in your own app.

Which to choose:

| Option | Best for | Runs on |
| :---- | :---- | :---- |
| Routines | Repeat work that fits in the cloud | Anthropic infrastructure |
| claude \-p | Jobs in your own scripts or pipelines | Your machine or CI |
| \--bare | CI runs that must be repeatable | Your CI |
| Agent SDK | Features inside your own product | Your application |

**Key lesson:** Start with routines and move to more control only when the job needs it.

8. # **GitHub Actions and Code Review**

Pull requests are where review and much of the busywork happen, so they are the natural place to hand work to Claude. There are two options:

| Aspect | Code Review (managed) | GitHub Action (DIY) |
| :---- | :---- | :---- |
| Purpose | PR review | Custom CI work beyond review |
| Setup | An admin turns it on in Claude Code admin settings | /install-github-app and a workflow file |
| Hosting | Anthropic | Your GitHub Actions runners |
| Output | Inline findings with suggested fixes and a severity summary | Commits, comments, reports |
| Fixes | Apply locally with /code-review \--fix | The agent can push commits |
| Approval | Never approves or blocks; humans decide | Depends on your configuration |

## **Code Review**

* Reviews the diff against the whole codebase, then deduplicates findings and ranks them by severity.  
* Triggers: when a PR opens, on every push, or only on an @claude review comment.  
* Research preview on Team and Enterprise plans.

## **The GitHub Action**

* Run /install-github-app (repo admin needed) to install the app and add the API key secret, then add .github/workflows/claude.yaml using anthropics/claude-code-action@v1.  
* Key inputs: trigger\_phrase (default @claude), prompt, claude\_args, and use\_bedrock or use\_vertex.  
* **Example:** a reviewer comments @claude asking it to implement a linked spec, and Claude pushes commits and explains them.  
* **Scheduled jobs:** a cron trigger for a daily rollup, plus workflow\_dispatch to run it manually.

## **Tuning unattended jobs**

* Cap the loop with \--max-turns.  
* Use a permission mode that never stops to ask, since nobody is there to answer.  
* Grant only the tools the job needs; report jobs should be read-only.

9. # **Trust It: Verifying Unsupervised Runs**

Verify in proportion to how little you watched. A short session you followed needs a glance; an unattended CI run needs a check that reconstructs what happened.

## **Practices**

* **Auto mode, not bypass:** keep the classifier as a safety net, but remember it checks danger, not correctness.  
* **Diff before summary:** run /code-review and read git diff yourself. Start with the files in the plan, then look for changes outside it. A tidy summary can hide an unexpected file.  
* **Tests as a gate:** a Stop hook runs the tests and refuses to end the turn on failure, and a PostToolUse hook lints and type checks after every edit. Exit 2 sends failures back for Claude to fix.  
* **Cold second opinion:** a fresh session or subagent with no memory of the build reviews the change and catches what the original run rationalized away.  
* **Headless runs:** judge them by the JSON result and exit code, not the narrative.

**Key lesson:** Work Claude did while you were not watching should never be accepted on Claude's word alone.

10. # **Plugins**

A plugin packages a Claude Code setup into one installable, versioned unit: skills, subagents, hooks, MCP server configs, LSP servers, monitors, themes and a small part of settings.json.

## **Installing**

* Install by name with /plugin install github@claude-plugins-official, then run /reload-plugins.  
* Add a team marketplace with /plugin marketplace add your-org/claude-plugins. Later installs resolve through it, and the Discover tab lists its plugins.  
* Public sources: the community marketplace (automated review) and the curated official marketplace.

## **Read before you install**

* A plugin runs code with your privileges, and its hooks fire on every matching tool call.  
* Check its hooks, agents, MCP servers and estimated context cost first. Reviewed is not the same as trusted.  
* Components run alongside yours: hooks stack, and skills, agents and commands are namespaced under the plugin name.  
* Only two settings.json keys are honored. The agent key can promote a plugin subagent to the main thread and change default behavior.

## **Packaging your own**

* Keep the working .claude layout: skill folders, agents/\*.md, hooks/hooks.json and .mcp.json.  
* Add .claude-plugin/plugin.json with a name (used as the namespace) and a version.  
* Publish through a team marketplace so everyone installs the same version.

11. # **Putting It All Together: A Trusted Hands-Off Workflow**

The nine lessons build one workflow: steer the work, configure Claude so it behaves the same way every time, automate the repeat work, then verify and share the setup.

## **The workflow at a glance**

Each layer builds on the one before:

| Layer | Tools | What it gives you |
| :---- | :---- | :---- |
| Steer | Plan mode, /compact, rewind, /goal, /loop, worktrees | Long sessions that stay on track |
| Configure | CLAUDE.md, skills, permission modes, hooks | Consistent behavior and enforced rules |
| Automate | Routines, claude \-p, Agent SDK, Code Review, GitHub Action | Work that runs without you starting it |
| Verify | Diff review, Stop and PostToolUse hooks, fresh-context review | Evidence instead of trust |
| Share | Plugins and a team marketplace | The same trusted setup for everyone |

## **Guidance, procedure or guarantee**

The most important decision in the course is where each rule lives:

* **CLAUDE.md:** short, specific conventions Claude should follow.  
* **Skills:** repeated procedures, starting with verification.  
* **Permission modes:** how much Claude may do without asking (auto for long work, dontAsk for CI).  
* **Hooks:** rules that must hold every time, such as blocking pushes to main or refusing to stop while tests fail.

## **Example: an overnight dependency upgrade**

How the pieces work together on one task:

* **Plan:** start in plan mode and approve a plan listing the packages and files to change.  
* **Run:** set /goal all tests pass and the type checker reports zero errors, in auto mode, inside its own worktree.  
* **Guardrails:** CLAUDE.md conventions apply, the verification skill runs when the work is done, a PostToolUse hook lints each edit and a Stop hook blocks finishing while tests fail.  
* **Review:** Code Review comments on the PR, you read the diff starting with the planned files, and a fresh subagent gives a second opinion.  
* **Automate next time:** turn the job into a weekly routine with /schedule, which pushes only to a claude/ branch.  
* **Share:** package the skill, hooks and settings as a plugin so teammates get the same setup.

## **Suggested adoption path**

* **Start:** plan mode, a lean CLAUDE.md and a verification skill.  
* **Enforce:** hooks for rules that must hold, and auto mode for long sessions.  
* **Scale:** worktrees, goals and loops for parallel and longer work.  
* **Automate:** Code Review, then routines, headless runs and the GitHub Action.  
* **Share:** package the setup as a plugin once it works.

**Key takeaway:** Trust in an unsupervised run comes from the setup, not from watching it: lean instructions, skills for procedures, hooks for guarantees, and verification scaled to how little you watched.

# **Building with the Claude API**

## **11th November 2026**

Course: [Claude Academy – Anthropic](https://academy.claude.com/courses/building-with-the-claude-api)

1. # **Introduction: Building Applications on the Claude API**

The course is for software engineers who want to integrate Claude into their own applications through the API. It assumes Python skills, basic JSON handling and an Anthropic API key. It runs about 9 hours: 67 lessons and 8 quizzes, ending with a final assessment.

It is organized in nine sections:

| Section | What it covers |
| :---- | :---- |
| Accessing Claude with the API | Requests, multi-turn chats, system prompts, temperature, streaming, structured output |
| Prompt evaluation | Test datasets, running evals, model-based and code-based grading |
| Prompt engineering | Clear and direct prompts, specific guidelines, XML tags, examples |
| Tool use | Tool schemas, tool results, multi-turn tool loops, the text editor and web search tools |
| RAG and agentic search | Chunking, embeddings, BM25 and hybrid retrieval |
| Features of Claude | Extended thinking, images, PDFs, citations, prompt caching, code execution and the Files API |
| Model Context Protocol | Building MCP servers and clients with tools, resources and prompts |
| Claude Code and computer use | Anthropic's own agent apps, extended with MCP servers |
| Agents and workflows | Parallelization, chaining and routing workflows, and agent design |

2. # **Accessing Claude with the API**

Every interaction is a request to the Messages API. The examples use the anthropic Python SDK, with the key stored as ANTHROPIC\_API\_KEY in a .env file that is listed in .gitignore.

## **Making a request**

client.messages.create() takes three required parameters:

| Parameter | Purpose |
| :---- | :---- |
| model | The Claude model to use, for example claude-sonnet-4-5 |
| max\_tokens | A safety cap on response length, not a target. Claude stops only if it reaches it. |
| messages | The conversation so far: a list of dictionaries, each with a role (user or assistant) and content |

message.content\[0\].text returns the generated text without the response metadata.

## **Multi-turn conversations**

* **No memory:** the API does not store conversation history. Each request is independent, and Claude sees only what you send.  
* **Keep the history yourself:** append each user message and each assistant reply to a list, and send the whole list with every request.  
* **Helpers:** add\_user\_message(), add\_assistant\_message() and chat() keep the calling code short.

## **Controlling the output**

* **System prompt:** the system parameter sets the role, tone and rules for the whole conversation, separate from the user's messages.  
* **Temperature (0 to 1):** low values make output predictable, high values make it varied. It changes the odds of each token but guarantees nothing.  
* **Streaming:** client.messages.stream() sends the reply in chunks as it is generated. Use text\_stream to show text live and get\_final\_message() to keep the complete reply.  
* **Structured data:** prefill the assistant message with an opening \`\`\`json fence and set \`\`\` as a stop sequence. Claude returns only the JSON, ready for json.loads(text.strip()).

Suggested temperature ranges:

| Range | Use for |
| :---- | :---- |
| 0.0 to 0.3 | Factual answers, coding, data extraction, content moderation |
| 0.4 to 0.7 | Summaries, educational content, problem-solving |
| 0.8 to 1.0 | Brainstorming, creative writing, marketing copy |

**Key lesson:** Claude is stateless. Your application owns the conversation history, and parameters like system, temperature and stop\_sequences shape each reply.

3. # **Prompt Evaluation**

Prompt evaluation replaces guesswork with a score. Instead of reading a few outputs and deciding a prompt looks better, you run it over a dataset and compare averages.

## **A typical eval workflow**

* **Draft a prompt:** write a baseline version.  
* **Build a dataset:** collect inputs that reflect real requests. Write them by hand or have Claude generate them.  
* **Run the prompt:** insert each input into the prompt template and get Claude's response.  
* **Grade:** a grader scores each input and response pair, usually from 1 to 10, and the scores are averaged.  
* **Change and repeat:** edit the prompt, rerun everything and compare the new average with the baseline. In the lesson, asking for more detail raised the average from 7.66 to 8.7.

## **Grader types**

There are three kinds of grader:

| Grader | Checks | Trade-off |
| :---- | :---- | :---- |
| Code | Length, required or banned words, valid JSON, Python or regex syntax | Fast and exact, but only for objective checks |
| Model | Quality, instruction following, completeness, safety | Flexible, but scores vary and each grade is another API call |
| Human | Anything | Most flexible, but slow and tedious |

## **Writing a model grader**

* Ask for a JSON object with strengths, weaknesses, reasoning and a score. Asking for reasoning keeps the grader from defaulting to middling scores around 6\.  
* Prefill a \`\`\`json fence and use a stop sequence so the result always parses.  
* For code output, combine the model score with a syntax score: 10 if json.loads, ast.parse or re.compile succeeds, 0 if not. A format field on each test case picks the validator.

**Key lesson:** The absolute score matters less than the trend. Keep the best-scoring prompt and keep iterating against the same dataset.

4. # **Prompt Engineering Techniques**

Each technique was measured with the eval pipeline from the previous section, so every change shows up as a score.

| Technique | What to do | Result in the lesson |
| :---- | :---- | :---- |
| Be clear and direct | Lead with the task in the first line, using an action verb (Write, Create, Generate) instead of a question | Score rose from 2.32 to 3.92 |
| Be specific | Add output guidelines (length, structure, required elements, tone) and, for complex tasks, process steps to follow | Meal-plan score rose from 3.92 to 7.86 |
| Structure with XML tags | Wrap large or mixed content in descriptive tags such as \<sales\_records\> or \<my\_code\> | Instructions stay separate from the data |
| Provide examples | Give one-shot or multi-shot input and output pairs, wrapped in tags such as \<sample\_input\> and \<ideal\_output\> | Sarcastic tweets stopped being read as positive |

## **Tips for examples**

* **Mine your evals:** use the highest-scoring outputs from earlier eval runs as examples.  
* **Explain why:** say what makes an example ideal, not just the pair itself.  
* **Cover corner cases:** add examples for the inputs Claude gets wrong, such as sarcasm.

**Key lesson:** Lead with a clear instruction, then add guidelines, structure and examples, and check each change with an eval.

5. # **Tool Use with Claude**

Tools let Claude reach information and actions outside its training data, such as live weather or a database. Claude never runs a tool itself: it asks for a call, your code runs it, and you send back the result.

## **The tool use flow**

* **Request:** send the user's question with the tool schemas in the tools parameter.  
* **Tool call:** if Claude needs data, the reply holds a text block and a tool\_use block with an id, the tool name and its input, and stop\_reason is "tool\_use".  
* **Run:** your code calls the function with the input arguments.  
* **Result:** send a user message with a tool\_result block, and Claude writes the final answer.

## **Tool schemas**

Each schema has three parts:

| Field | Content |
| :---- | :---- |
| name | A clear identifier, such as get\_weather |
| description | Three or four sentences: what the tool does, when to use it and what it returns |
| input\_schema | A JSON Schema object that describes each argument in detail |

Claude can write the schema for you from the function code and Anthropic's tool use docs. Naming it function\_name\_schema and typing it as ToolParam keeps the code organized.

## **Sending tool results**

* **tool\_use\_id:** must match the id of the tool\_use block. When Claude asks for several tools in one reply, each call has its own id.  
* **content:** the tool's output as a string.  
* **is\_error:** set to true when the tool failed, so Claude can react to it.  
* **Full history:** the follow-up request carries the user message, the assistant's tool\_use message and the tool\_result message, plus the tool schemas again.

## **Multi-turn tool loops**

* Call Claude, append response.content (all blocks) to the history, run every requested tool, send the results and repeat.  
* Stop when stop\_reason is anything other than "tool\_use".  
* A run\_tool() router maps tool names to functions, so a new tool needs only a function, a schema and one new case.

## **Built-in tools and streaming**

Three more tool features:

| Feature | How it works |
| :---- | :---- |
| Text editor tool | Claude already knows the schema, sent as a short stub such as text\_editor\_20250124. You implement the commands: view, replace text, create, insert and undo. |
| Web search tool | Runs on Anthropic's side (type web\_search\_20250305) once enabled in the console. max\_uses caps the searches, allowed\_domains limits the sources, and replies include citations. |
| Fine-grained tool calling | Streams tool arguments as Claude writes them, without server-side JSON validation, so your code must handle invalid JSON. |

**Key lesson:** Claude decides when to call a tool; your code decides what the tool does. Keep the whole history, match every result to its id, and loop until stop\_reason is no longer "tool\_use".

6. # **RAG and Agentic Search**

Retrieval Augmented Generation (RAG) finds the parts of a large document set that are relevant to a question and puts only those in the prompt, instead of sending everything.

## **Chunking strategies**

Poor chunks add irrelevant context and lead to wrong answers. There are four ways to split text:

| Strategy | How it splits | Best for |
| :---- | :---- | :---- |
| Size-based | Equal-length pieces, ideally with overlap | Any content, including code; a reliable fallback |
| Structure-based | Document markers such as Markdown headers | Documents with a guaranteed format |
| Sentence-based | Groups of sentences, optionally overlapping | Most prose |
| Semantic-based | Consecutive sentences grouped by meaning | Most relevant chunks, but expensive and complex |

## **The RAG flow**

* **Preprocess once:** chunk the text, turn each chunk into an embedding with an embedding model, and store the normalized vectors in a vector database.  
* **Query:** embed the user's question with the same model and find the closest chunks.  
* **Prompt:** send the question together with the retrieved chunks to Claude.  
* **Similarity:** cosine similarity runs from \-1 to 1, and values near 1 mean very similar. Cosine distance is 1 minus the similarity.

## **Hybrid search with BM25**

* **The gap:** semantic search finds related meaning but can miss exact terms such as an incident ID (INC-2023-Q4-011).  
* **BM25:** lexical search that weights rare terms more than common ones, so IDs and technical phrases rank well.  
* **Multi-index retriever:** send each query to the vector index and the BM25 index, then merge the rankings with reciprocal rank fusion. Each document scores the sum of 1/(k \+ rank) across indexes; k=60 is common.  
* **Extensible:** any index with the same add\_document() and search() interface can join the fusion.

**Key lesson:** Chunk quality decides answer quality. Combine semantic and lexical search so both meaning and exact terms are found.

7. # **Features of Claude**

Beyond plain text, the API supports longer reasoning, images and PDFs, citations and server-side code execution.

## **Extended thinking**

* Enable it with thinking: {"type": "enabled", "budget\_tokens": N}. The minimum budget is 1024, and max\_tokens must be larger than the budget.  
* Replies hold thinking blocks (the reasoning, with a signature that proves it was not changed), redacted thinking blocks when safety systems flag the reasoning, and text blocks with the answer.  
* It costs more, adds latency, does not work with prefilling and limits temperature. Use it only when an optimized prompt is still not accurate enough.

## **Images and PDFs**

* **Images:** an image block with a base64 or URL source and a media\_type such as image/png, sent with a text block in the same user message.  
* **Image limits:** 100 images per request, 5 MB each, 8000 px per side (2000 px when sending several). Cost is about width × height / 750 tokens.  
* **Prompting images:** use the same techniques as for text: step-by-step instructions, one-shot examples and smaller sub-tasks.  
* **PDFs:** a document block with media\_type application/pdf. Claude reads the text, images, charts and tables.

## **Citations**

Add a title and citations: {"enabled": true} to a document block. Each citation returns the cited text, the document and its location: page numbers for PDFs, character positions for plain text. Use them when users need to check claims against the source.

## **Code execution and the Files API**

* **Files API:** upload a file once, get a file ID, and reference the ID instead of sending base64 again.  
* **Code execution:** a server-side tool where Claude runs Python in an isolated container with no network access, so files go in through the Files API.  
* **Output:** generated files such as plots come back as file IDs you can download.

**Key lesson:** Reach for extended thinking last, after the prompt itself. Citations make answers checkable, and the Files API avoids resending large inputs.

8. # **Prompt Caching**

Prompt caching stores the work Claude does processing the start of a prompt, so later requests with identical content are faster and cheaper.

## **Rules of prompt caching**

* **Not automatic:** add cache\_control: {"type": "ephemeral"} to a block. This needs the longhand block form, for example a system prompt written as a list of text blocks.  
* **Prefix match:** everything up to and including the breakpoint is cached, and a later request reuses it only if that part is identical. Adding a single word forces a full reprocess.  
* **Order:** tools, then system prompt, then messages. A change early in that order invalidates everything after it.  
* **Limits:** up to 4 breakpoints per request, and at least 1024 tokens of cached content in total.  
* **Lifetime:** 5 minutes by default, reset on each use. A 1-hour cache costs more to write.

Where breakpoints work well:

| Breakpoint on | Effect |
| :---- | :---- |
| The last tool definition | Caches all tool schemas |
| The system prompt | Caches content that rarely changes between requests |
| A later message | Caches all earlier messages too, useful for long conversations |

## **Checking the cache**

The usage field shows cache\_creation\_input\_tokens on the request that writes the cache and cache\_read\_input\_tokens on requests that read it. If only the system prompt changes, the tools are still read from the cache and the system prompt is written again.

**Key lesson:** Put stable content first (tools, then the system prompt) and changing content last, so the cached prefix stays identical between requests.

9. # **Model Context Protocol**

MCP is a communication layer that moves tool definitions and their execution out of your application and into MCP servers. Your application is the MCP client. Instead of writing every GitHub tool yourself, you connect to a GitHub MCP server, often published by the service provider.

MCP does not replace tool use: tool use is how Claude calls tools, and MCP decides who builds and maintains them.

## **How client and server talk**

* **Transport:** usually standard input and output on the same machine, but HTTP, WebSockets and others also work.  
* **Messages:** ListToolsRequest returns the server's tools, and CallToolRequest runs one with arguments.  
* **Flow:** your app gets the tool list from the client and sends it to Claude with the query. When Claude asks for a tool, the client forwards the call to the server, and the result goes back to Claude.

## **The three server primitives**

A server can expose three kinds of capability:

| Primitive | Defined with | Purpose |
| :---- | :---- | :---- |
| Tools | @mcp.tool | Actions Claude can call. The SDK builds the schema from type hints and Field descriptions. |
| Resources | @mcp.resource("docs://documents/{doc\_id}") | Data the app reads, like GET handlers: direct (static URI) or templated (URI with parameters) |
| Prompts | @mcp.prompt | Tested instruction templates that return messages ready to send to Claude |

## **Building and testing**

* **Server:** FastMCP from the Python SDK creates the server. Raise a clear ValueError so Claude understands a failure.  
* **Inspector:** mcp dev mcp\_server.py opens a browser inspector on port 6277 to run tools, read resources and check prompts without an app.  
* **Client:** a wrapper around ClientSession exposes list\_tools(), call\_tool(), list\_prompts() and get\_prompt(), plus resource reads.

**Key lesson:** MCP separates who builds integrations from who uses them. Test each server in the inspector before wiring it into a client.

10. # **Claude Code and Computer Use**

Claude Code and Computer Use are Anthropic's own agents. They rely on the same ideas as the rest of the course: tools, multi-step work and checking the environment.

* **Claude Code:** a terminal coding assistant. /init scans the project and writes CLAUDE.md, \# adds a quick rule to it, and /clear resets the context.  
* **Workflows:** give the relevant files as context, ask for a plan without code, then implement. Or brainstorm test cases first and write code that passes them.  
* **MCP in Claude Code:** claude mcp add documents uv run main.py registers a server, and Claude Code connects to it at startup. Servers exist for Sentry, Playwright, Figma, Atlassian and Slack.  
* **Computer Use:** a set of tools that lets Claude operate a full desktop, browsing and using apps, for tasks that need a visual interface.

**Key lesson:** More context and structure give better results: a good CLAUDE.md, a plan before code, and MCP servers for the systems the team uses.

11. # **Agents and Workflows**

Both handle tasks a single request cannot. A workflow is a fixed series of Claude calls; an agent gets a goal and tools and decides the steps itself.

| Pattern | How it works | Use when |
| :---- | :---- | :---- |
| Evaluator-optimizer | A producer creates output, a grader checks it, and feedback loops back until it passes | Output can be checked, such as a rendered CAD model against the source image |
| Parallelization | Split one task into independent requests that run at the same time, then combine the results | One prompt has too many criteria to weigh |
| Chaining | Run sequential steps, each focused on one part, with code checks in between | Claude ignores some constraints in a long prompt |
| Routing | Classify the input first, then send it to a specialized prompt | Requests are diverse but fall into clear categories |

## **Designing agents**

* **Workflows first:** use one when you can picture the steps. Agents are more flexible but less reliable and cost more.  
* **General tools:** prefer abstract tools that combine, like Claude Code's bash, read, write and grep, over narrow single-purpose tools.  
* **Environment inspection:** give Claude a way to see results, such as a screenshot after each computer use action or reading a file before editing it. Ask how Claude will know an action worked.

**Key lesson:** Start with the simplest workflow that solves the task, and move to an agent only when the steps cannot be known in advance.

12. # **Putting It All Together**

The sections build from a single request to a full application:

| Layer | Tools | What it gives you |
| :---- | :---- | :---- |
| Basics | messages.create, history, system prompt, temperature, streaming | A working chat with controlled output |
| Quality | Evals, graders, prompt techniques | Measured, repeatable prompt improvements |
| Capabilities | Tool use, RAG, extended thinking, images, PDFs, citations | Claude working with live data and your documents |
| Cost | Prompt caching, Files API | Faster and cheaper repeated requests |
| Integration | MCP servers and clients, Claude Code | **Reusable integrations instead of hand-written tools** |
| Architecture | Workflows and agents | Multi-step tasks with the right level of autonomy |

**Key takeaway:** Treat Claude as a stateless service you call well: manage the history, measure prompts with evals, give it tools and context, cache what repeats, and pick the simplest workflow that works.