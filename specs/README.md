# Design Specifications

> **Branch**: `feature/design-specs`  
> **Purpose**: Discuss, iterate, and approve each spec individually before any implementation begins.  
> **Process**: Each spec goes through Draft → Review → Approved. Nothing gets built until approved.

---

## Spec Index

| # | Spec | Status | Description |
|---|------|--------|-------------|
| 1 | [TTS & Voice — Gemini Live Audio](./spec-01-tts-gemini.md) | 📝 Draft | Replace gTTS with Gemini TTS for fun, engaging, human-like narration |
| 2 | [AI-Generated Visuals — Gemini Image](./spec-02-visuals-gemini.md) | 📝 Draft | Replace Pexels stock photos with Gemini-generated unique visuals |
| 3 | [Agentic Quality Pipeline](./spec-03-agentic-quality.md) | 📝 Draft | Generator Agent + Reviewer Agent for copyright, trends, and quality |
| 4 | [YouTube Shorts Pipeline](./spec-04-shorts-pipeline.md) | 📝 Draft | Generate 2 Shorts alongside every Long video |
| 5 | [Multi-Channel Architecture](./spec-05-multi-channel.md) | 📝 Draft | Config-driven pipeline supporting N channels with separate credentials |
| 6 | [Trend Research Producer Agent](./spec-06-trend-agent.md) | 📝 Draft | Weekly trend research + monthly niche discovery with owner approval |
| 7 | [SEO & Content Optimization](./spec-07-seo-optimization.md) | 📝 Draft | Click-worthy titles, optimized descriptions, editor prompt chain |

---

## Decision Log

Decisions captured from the analysis report Q&A:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| TTS Provider | **Gemini** | Lower cost, natural voices, emotion via prompts |
| Image Generation | **Gemini Image API** | Same API key, unique visuals, no Pexels dependency |
| First New Channel | **Spacepedia** | More variety, more interesting topics |
| Review Mode | **Human-in-the-loop** until production-ready | Agent generates → Reviewer agent checks → Owner approves |
| Trend Agent Cadence | **Weekly** (topics) + **Monthly** (new niche) | Owner reviews and approves before pipeline picks up |
| YouTube Accounts | **Separate Google accounts** per channel | Quota isolation, risk isolation. Single account for now, multi-account ready |
| Priority | **TTS + Visuals upgrade first** | Highest demonetization risk; foundation for everything else |
| End Goal | **Fully autonomous** multi-channel content factory | Human-in-the-loop is temporary during development |
