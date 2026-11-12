### :wave: Hi

I'm Victor, a passionate gamer, modder and software engineer based in Grenoble 🇫🇷, born in 1999.

I like building things that prove themselves: infrastructure rebuilt from Git, a decompiler whose output is recompiled and run against the original, an AI agent that cites its sources.

### :compass: How I work

AI agents write most of my code these days. My part is what they can't be trusted with alone: the spec, the architecture, and the checks that decide whether their work is right. Depending on the project, that's tests that failed before the fix, mutation testing, oracles, or CI gates out of the agent's reach. When the checks pass and something still feels off, I dig until I know why.

---

### :star: Featured work

**☁️ Infrastructure**

- [**Homelab**](https://github.com/McReaper/Homelab): a k3s cluster on an OVH VPS, rebuilt from Git. OpenTofu provisions the server and the DNS, Argo CD (app of apps) deploys the rest, and secrets live encrypted in the repo (SOPS + age). cert-manager gets a wildcard Let's Encrypt certificate over DNS-01, Traefik serves it, and Authelia (OIDC SSO + MFA) stands in front. CI scans it with Trivy, Renovate keeps it current.
- [**DockerTooling**](https://github.com/McReaper/DockerTooling): the container I run it from (kubectl, helm, tofu, k9s, sops…), built and Trivy-gated by CI, so a machine only needs Docker.

**🤖 AI agents**

- [**T7 Companion**](https://github.com/McReaper/t7_companion): ten years of the Black Ops III modding community's knowledge, a skill for each craft and a headless build of the game's toolchain, for an AI agent. One Go binary serves it over MCP, offline, and every search hit carries its source and reliability so the agent can cite it.
- [**Rumblestrip**](https://github.com/McReaper/rumblestrip-go): an anti-drift kit for AI-written Go. The agent writes the spec in plain English for a human to approve, then the code, and about twenty checks it can't switch off decide whether it merges.

**🔬 Reverse engineering**

- [**T7 DXBC**](https://github.com/McReaper/t7_dxbc): a pure-Go disassembler and decompiler for Black Ops III's compiled shaders. Its disassembly matches Microsoft's on all 26,047 shaders of the mod tools, and each decompilation is recompiled, then judged by two oracles, one of them a CPU simulator that runs both shaders on the same random inputs.
- [**T7 Radiant Bridge**](https://github.com/McReaper/t7_radiant_bridge): a C++17 plugin for the game's level editor that lets any program read, edit (with undo) and capture the open map over a named pipe.

**🗣️ Talks & notes**

- [**REX: Building a RAG with LLMs**](https://github.com/McReaper/building-a-rag-with-llms) 🇫🇷: a Pecha Kucha talk at a Grenoble meetup on agentic AI. A local, deterministic pipeline by default, an agent only where the pipeline demonstrably fails.
- [**AlpOSS 2026**](https://github.com/McReaper/alposs2026_personnal_summary): my notes on the talks of this open-source conference in Échirolles.

**🎓 Before the agents**

- [**Internship, 2021**](https://github.com/McReaper/InternshipINFO4) ([report](https://github.com/McReaper/InternshipINFO4Report)): *Language Design for Linux I/O Scheduling*, evolving the compiler of the PhaistOS DSL to generate Linux kernel modules in C, benchmarked on SSDs.
- [**Panzer n' Parser**](https://github.com/McReaper/PanzerNParser): a Java survival-strategy game built in four weeks by a team of seven at Polytech Grenoble.

For my professional experience and education, see [LinkedIn](https://www.linkedin.com/in/victor-malod/).

### :wrench: Mods

- **Black Ops III**: [T7 Companion 🤖](https://github.com/McReaper/t7_companion), my [workshop 📥](https://steamcommunity.com/id/mcreaper/myworkshopfiles/?appid=311210) and my [workspace 🛠️](https://github.com/McReaper/t7_workspace)
- **Single Player Tarkov**: [my mods](https://sp-mod.com/user/127693/reapy#mods)

### :grey_question: About me

<details>
<summary>:sparkling_heart: Favorite Games</summary>

1. The Last of Us
2. The Last of Us Part II
3. Escape From Tarkov
4. DayZ
5. World Of Warcraft Classic
6. Dying Light
7. Dishonored
8. Skyrim
9. God Of War
10. God Of War Ragnarock
> And many more ... Like competitive games that I try to forget about, you know :wink:

</details>

<details>
<summary>:guitar: Music</summary>

- Instrumental Heavy Metal :metal:, I love very niche bands like:
  - Deaf Election
  - DeathKite
  - Sightless in Shadow
  - No Sons of Mine
  - Off Cuts
  - They Fall
  - Under Earth
  - For Giants
  - Andrew Hulshult
- US Rap (Logic and Eminem mostly)
- Synthwave (Danger, WaveShaper, ToneBox, DEADLIFE, Nightstop, Carpenter Brut ...)
- Drum N Bass (mostly for fun, thanks to Venjent)

</details>

<details>
<summary>:joy: Funny quotes</summary>

A few [quotes about our job](https://gist.github.com/McReaper/5ad72f2f6b572f7d6d19ceeea8ac32f1) that are sad but true.

</details>

### :inbox_tray: Contacts

- :mailbox_with_mail: Reach me through [LinkedIn](https://www.linkedin.com/in/victor-malod/) for professional opportunities.
- :mailbox_closed: You can try to reach me on Discord: `reapy`, but there is a low chance I accept your friend request if we don't share contacts/servers.

---

<p align="center"><img src="https://komarev.com/ghpvc/?username=McReaper&label=Profile%20views&color=0e75b6&style=flat" alt="McReaper"/></p>
