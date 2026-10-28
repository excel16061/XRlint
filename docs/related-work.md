# Related work and justification

**Citation rule for this document.** I list only work whose content I checked in its paper,
abstract page or official listing. Each entry says how I checked it. This is not an exhaustive
literature review, so I do not claim XRLint is the "first" of anything.

## 1. Why this project fits Prof. Farrukh's research

Prof. Farrukh leads the SPECT Lab (Security and Privacy of Emerging Computing Technology) at
UC Irvine. Her homepage describes her work as investigating security and privacy threats in
emerging computing platforms, using system design, machine learning and human-centered
methods [homepage, checked]. The XR line of her work includes the four papers below.

| Paper (checked) | What it does | Link to XRLint |
|---|---|---|
| **Shadowed Realities** (Mukherjee, Mohamed, Arunasalam, Farrukh, Celik; USENIX Security 2025) [full text read] | Taxonomy of WebXR UI attacks built from 14 security-sensitive UI properties, five new attacks, a logging framework with four interaction metrics, a 100-participant user study, and developer guidelines. | XRLint's rules are a direct static translation of this paper's properties and guidelines. |
| **Relay and Betray** (Ali, Farrukh; USENIX Security 2026) [full text read] | Client-side trust in multi-user MR apps; 20 apps; surveillance, tampering, safety circumvention, disruption, impersonation. | The same theme (untrusted code sharing one immersive scene), in the multi-user setting. XRLint does not cover multi-user XR. |
| **LocIn** (Farrukh et al.; USENIX Security 2023) [full text read] | Infers a user's indoor location type from MR spatial maps. | Same lab focus on XR-specific data and attack surfaces. Different technique (ML inference rather than UI). |
| **VR firmware** (Simhadri, Xiong, Farrukh, Zhang; CCS 2025) [full text read] | Longitudinal static analysis of 300+ Quest and Pico firmware versions. | Methodological precedent: large-scale **static** security measurement of XR software. XRLint applies static checks at the web-application layer. |

The two related lab outputs below are listed on her publications page, but **I could not
open their PDFs** (download failed). I only know their titles and the summary below; read them
before any meeting.

- *Towards Secure User Interaction in WebXR* (Mukherjee, Arunasalam, Farrukh, Aburas, Celik;
  HumanSys workshop 2025) [title and authors only].
- *Demo: UI Based Attacks in WebXR* (MobiSys 2025) [summary read via an NSF repository copy].
  It demonstrates five of the attacks in an A-Frame shooting game. It is not a detection tool.

## 2. What Shadowed Realities lists as future work

From the paper's Discussion (§8) [full text read]:

1. *"Future work will focus on automated tools to detect dark patterns in XR UI designs."*
   This sentence follows the developer guidelines, where the paper suggests that app
   developers audit their apps with its list of UI properties. **XRLint is a small step toward
   this item**, and is static only.
2. Extending the logging framework and metrics to standalone AR/VR headsets (beyond WebXR).
3. Dark patterns in **multi-user** WebXR apps.
4. Dark patterns using **hand-tracking** input.

The paper's guidelines (§8) are also the basis of several rules:
- validate input sources (`P5`, `P3`);
- block auxiliary-screen redirection by overriding `window.open` (`P8`);
- monitor enter/exit of immersive mode (`P9`, `P8`);
- watch ads' position, size and opacity changes (`P2-js`, `P7`);
- avoid clickable third-party objects behind unclickable ones (`P12`).

## 3. How XRLint differs from existing work and tools

| Work (checked) | What it is | How XRLint differs |
|---|---|---|
| **Shadowed Realities logging framework + metrics** (2025) [full text] | Runtime logging in A-Frame apps; four metrics (Presence, Safe Engagement, Malicious Attention, Blind Spot Rendering Fraction) computed from real user sessions. Developers must specify task and dark-pattern objects. | XRLint needs no users, no headset and no labels of which object is the "dark pattern". It runs on source before deployment. It cannot tell whether an attack *worked*; the logging framework can. They are complementary. |
| **Purdue "Dynamic Policy Enforcement in WebXR"** (Celik's group; IRB study page, last updated April 2026) [study announcement read] | The group is building a **runtime system that detects UI manipulation in WebXR** and is evaluating it with Meta Quest 3 users. No paper found yet. | This is the closest work and comes from the same research line (Prof. Farrukh is a co-author of Shadowed Realities). XRLint is **static**: earlier in the pipeline, cheaper, but blind to runtime-built scenes. Be ready to describe XRLint as a complement to a runtime system, not an alternative. |
| **Cheng et al., "When the User Is Inside the User Interface"** (USENIX Security 2024) [USENIX abstract page read] | Defines three AR UI security properties (same space, invisibility, synthetic input) and tests five proof-of-concept attacks across ARCore, ARKit, HoloLens, Oculus and WebXR. | An empirical platform study, not a checker. Three of XRLint's rules (P4, P2, P3) correspond to its three properties, via Shadowed Realities. |
| **AdCube** (Lee, Lee, Kim, Jana, Shin, Son; USENIX Security 2021) [USENIX abstract page read] | Four WebVR ad-fraud attacks, plus a defense that lets publishers specify and enforce what third-party ad code may do (236 ms load latency on nine demo sites). | AdCube *enforces* a policy at runtime. XRLint only *reports* risky properties in source. AdCube is a natural "what to do about the findings" answer. |
| **Krauß et al., "What Makes XR Dark?"** (ACM TOCHI 2024) [publisher summary read] | Expert co-design workshops producing XR dark-pattern scenarios and four XR-specific enabling properties (perception, spatiality, physical/virtual barriers, device sensing). | A conceptual and HCI characterisation. No code analysis. |
| **AidUI** (Mansur, Salma, Awofisayo, Moran; ICSE 2023) [conference abstract read] | Recognises 10 dark patterns in **2D mobile and web screenshots** from visual and textual cues (precision 0.66, recall 0.67). | Works on 2D screenshots. XRLint works on 3D scene source and targets security-sensitive *interaction* properties (who receives a click), which a screenshot cannot show. |

In a short search I did not find a static analyzer specifically for WebXR or A-Frame UI
security properties. That is a weak statement: I did not do a full literature review, so do
not say "first".

## 4. Justification in one paragraph

Shadowed Realities shows the attacks work and go unnoticed, and it gives developers a list of
risky properties plus guidelines. A list is only useful if someone can find where those
properties occur in real code. XRLint turns the list into checks with a file, a line and a
reason. It measures honestly how often the properties appear in benign code (often) and what a
static view cannot see (anything built at runtime). That negative result is itself useful for
the paper's future-work item. It suggests detection needs a runtime component, which is the
direction the original authors' group is now taking, while static checks remain a cheap first
filter for code review.

## References (all checked as described above)

- H. Farrukh, homepage and publication list: https://habiba-farrukh.github.io/
- C. Mukherjee, R. Mohamed, A. Arunasalam, H. Farrukh, Z. B. Celik. Shadowed Realities: An Investigation of UI Attacks in WebXR. USENIX Security 2025. https://habiba-farrukh.github.io/files/ShadowedRealities.pdf ; artifacts: https://doi.org/10.6084/m9.figshare.28271207
- C. Mukherjee et al. Demo: UI Based Attacks in WebXR. MobiSys 2025. https://par.nsf.gov/servlets/purl/10663427
- M. Ali, H. Farrukh. Relay and Betray: Exploiting Client-Side Authority in Multi-User Mixed Reality. USENIX Security 2026. https://mutahar789.github.io/assets/files/multi-user_mr_sec.pdf
- H. Farrukh, R. Mohamed, A. Nare, A. Bianchi, Z. B. Celik. LocIn: Inferring Semantic Location from Spatial Maps in Mixed Reality. USENIX Security 2023. https://habiba-farrukh.github.io/files/LocIn.pdf
- V. S. Simhadri, Y. Xiong, H. Farrukh, X. Zhang. Virtual Reality, Real Problems: A Longitudinal Security Analysis of VR Firmware. CCS 2025. https://habiba-farrukh.github.io/files/VRFirmware.pdf
- K. Cheng et al. When the User Is Inside the User Interface: An Empirical Study of UI Security Properties in Augmented Reality. USENIX Security 2024. https://usenix.org/conference/usenixsecurity24/presentation/cheng-kaiming
- H. Lee, J. Lee, D. Kim, S. Jana, I. Shin, S. Son. AdCube: WebVR Ad Fraud and Practical Confinement of Third-Party Ads. USENIX Security 2021. https://usenix.org/conference/usenixsecurity21/presentation/lee-hyunjoo
- V. Krauß et al. What Makes XR Dark? Examining Emerging Dark Patterns in Augmented and Virtual Reality through Expert Co-Design. ACM TOCHI 2024. https://www.deceptive.design/articles/what-makes-xr-dark-examining-emerging-dark-patterns-in-augmented-and-virtual-reality-through-expert-co-design
- S M H. Mansur, S. Salma, D. Awofisayo, K. Moran. AidUI: Toward Automated Recognition of Dark Patterns in User Interfaces. ICSE 2023. https://conf.researchr.org/details/icse-2023/icse-2023-technical-track/192/AidUI-Toward-Automated-Recognition-of-Dark-Patterns-in-User-Interfaces
- Purdue CS, "Dynamic Policy Enforcement in WebXR" user-study announcement: https://www.cs.purdue.edu/corporate/announcements/userstudy_2026_16.html
