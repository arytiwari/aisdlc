# Project Codebase Snapshot

This document lists every source file currently tracked in the repository along with its full contents for quick reference.

## File: README.md
```markdown
# aisdlc
Showcase of how AI based SDLC works
```

## File: vedic_chart.html
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AstroChart Wheel Demo</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {
      color-scheme: light;
      --bg-top: #f6f1eb;
      --bg-bottom: #d9c9b5;
      --rim: #3f2c1c;
      --accent: #c89235;
      --house: rgba(255, 255, 255, 0.82);
      --inner-ring: #f4e3c5;
      --planet: #2a1a11;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: "Inter", "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background: radial-gradient(circle at 50% 25%, rgba(255, 255, 255, 0.85), transparent 60%),
                  linear-gradient(180deg, var(--bg-top), var(--bg-bottom));
    }

    main {
      display: grid;
      gap: 24px;
      padding: clamp(20px, 6vw, 48px);
      width: min(100%, 960px);
    }

    h1 {
      margin: 0;
      text-align: center;
      font-weight: 600;
      color: #2a1a11;
      letter-spacing: 0.04em;
    }

    canvas {
      width: min(100%, 720px);
      height: auto;
      filter: drop-shadow(0 22px 55px rgba(0, 0, 0, 0.18));
      border-radius: 24px;
      background: rgba(255, 255, 255, 0.96);
    }

    .note {
      text-align: center;
      color: rgba(42, 26, 17, 0.74);
      font-size: 0.95rem;
    }
  </style>
</head>
<body>
  <main>
    <h1>AstroChart Wheel Rendered with Vanilla Canvas</h1>
    <canvas id="chart" width="900" height="900" role="img" aria-label="Circular birth chart with zodiac houses"></canvas>
    <p class="note">Demonstrates a static rendering inspired by the <strong>AstroChart</strong> library using programmatic drawing only.</p>
  </main>

  <script>
    const canvas = document.getElementById("chart");
    const ctx = canvas.getContext("2d");
    const size = canvas.width;
    const center = size / 2;

    const zodiac = [
      { name: "Aries", glyph: "\u2648", degree: 18 },
      { name: "Taurus", glyph: "\u2649", degree: 46 },
      { name: "Gemini", glyph: "\u264A", degree: 83 },
      { name: "Cancer", glyph: "\u264B", degree: 112 },
      { name: "Leo", glyph: "\u264C", degree: 137 },
      { name: "Virgo", glyph: "\u264D", degree: 182 },
      { name: "Libra", glyph: "\u264E", degree: 212 },
      { name: "Scorpio", glyph: "\u264F", degree: 244 },
      { name: "Sagittarius", glyph: "\u2650", degree: 276 },
      { name: "Capricorn", glyph: "\u2651", degree: 315 },
      { name: "Aquarius", glyph: "\u2652", degree: 332 },
      { name: "Pisces", glyph: "\u2653", degree: 352 }
    ];

    const planets = [
      { name: "Sun", glyph: "\u2609", degree: 120 },
      { name: "Moon", glyph: "\u263D", degree: 92 },
      { name: "Mercury", glyph: "\u263F", degree: 145 },
      { name: "Venus", glyph: "\u2640", degree: 178 },
      { name: "Mars", glyph: "\u2642", degree: 213 },
      { name: "Jupiter", glyph: "\u2643", degree: 255 },
      { name: "Saturn", glyph: "\u2644", degree: 305 },
      { name: "Rahu", glyph: "\u260A", degree: 45 },
      { name: "Ketu", glyph: "\u260B", degree: 225 }
    ];

    const toRad = (deg) => (deg - 90) * (Math.PI / 180);

    function drawRing(radius, thickness, fillStyle) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(center, center, radius, 0, Math.PI * 2);
      ctx.strokeStyle = "transparent";
      ctx.lineWidth = 1;
      ctx.fillStyle = fillStyle;
      ctx.fill();
      ctx.restore();

      if (thickness > 0) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(center, center, radius, 0, Math.PI * 2);
        ctx.lineWidth = thickness;
        ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue("--rim").trim();
        ctx.stroke();
        ctx.restore();
      }
    }

    function drawHouseLines() {
      ctx.save();
      ctx.lineWidth = 2.4;
      ctx.strokeStyle = "rgba(63, 44, 28, 0.6)";
      for (let i = 0; i < 12; i++) {
        const angle = (Math.PI * 2 * i) / 12;
        const x = center + Math.cos(angle) * 360;
        const y = center + Math.sin(angle) * 360;
        ctx.beginPath();
        ctx.moveTo(center, center);
        ctx.lineTo(x, y);
        ctx.stroke();
      }
      ctx.restore();
    }

    function drawZodiacSlices() {
      for (let i = 0; i < 12; i++) {
        const start = (Math.PI * 2 * i) / 12;
        const end = (Math.PI * 2 * (i + 1)) / 12;
        ctx.beginPath();
        ctx.moveTo(center, center);
        ctx.arc(center, center, 390, start, end);
        ctx.closePath();
        ctx.fillStyle = i % 2 === 0 ? "rgba(255, 255, 255, 0.72)" : "rgba(248, 229, 198, 0.76)";
        ctx.fill();
      }
    }

    function drawHouseNumbers() {
      ctx.save();
      ctx.fillStyle = "rgba(63, 44, 28, 0.85)";
      ctx.font = "600 22px 'Inter', 'Helvetica Neue', Arial";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      for (let i = 0; i < 12; i++) {
        const angle = ((i + 0.5) * Math.PI * 2) / 12;
        const x = center + Math.cos(angle) * 235;
        const y = center + Math.sin(angle) * 235;
        ctx.fillText(String(i + 1), x, y);
      }
      ctx.restore();
    }

    function drawZodiacGlyphs() {
      ctx.save();
      ctx.fillStyle = "rgba(42, 26, 17, 0.85)";
      ctx.font = "700 44px 'Noto Sans Symbols 2', 'Segoe UI Symbol', sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      zodiac.forEach((sign, index) => {
        const angle = ((index + 0.5) * Math.PI * 2) / 12;
        const x = center + Math.cos(angle) * 325;
        const y = center + Math.sin(angle) * 325;
        ctx.fillText(sign.glyph, x, y);
      });
      ctx.restore();
    }

    function drawPlanets() {
      ctx.save();
      ctx.font = "600 28px 'Noto Sans Symbols 2', 'Segoe UI Symbol', sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      planets.forEach((p) => {
        const angle = toRad(p.degree);
        const r = 180;
        const x = center + Math.cos(angle) * r;
        const y = center + Math.sin(angle) * r;

        ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--planet").trim();
        ctx.beginPath();
        ctx.arc(x, y, 22, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 255, 255, 0.92)";
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "rgba(63, 44, 28, 0.4)";
        ctx.stroke();

        ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--planet").trim();
        ctx.fillText(p.glyph, x, y);
      });
      ctx.restore();
    }

    function drawRadialLabels() {
      ctx.save();
      ctx.fillStyle = "rgba(63, 44, 28, 0.7)";
      ctx.font = "500 16px 'Inter', 'Helvetica Neue', Arial";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      zodiac.forEach((sign) => {
        const angle = toRad(sign.degree);
        const x = center + Math.cos(angle) * 420;
        const y = center + Math.sin(angle) * 420;
        ctx.fillText(sign.name, x, y);
      });
      ctx.restore();
    }

    function drawChart() {
      ctx.clearRect(0, 0, size, size);

      drawRing(420, 10, "rgba(255, 255, 255, 0.75)");
      drawRing(300, 8, getComputedStyle(document.documentElement).getPropertyValue("--inner-ring").trim());

      drawZodiacSlices();
      drawHouseLines();
      drawHouseNumbers();
      drawZodiacGlyphs();
      drawPlanets();
      drawRadialLabels();

      ctx.save();
      ctx.beginPath();
      ctx.arc(center, center, 110, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(255, 255, 255, 0.94)";
      ctx.fill();
      ctx.lineWidth = 1.4;
      ctx.strokeStyle = "rgba(63, 44, 28, 0.35)";
      ctx.stroke();

      ctx.fillStyle = "rgba(42, 26, 17, 0.82)";
      ctx.font = "600 20px 'Inter', 'Helvetica Neue', Arial";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("Sample Natal Chart", center, center - 12);
      ctx.font = "500 16px 'Inter', 'Helvetica Neue', Arial";
      ctx.fillText("Generated with Canvas", center, center + 12);
      ctx.restore();
    }

    drawChart();
  </script>
</body>
</html>

```

## File: LICENSE
```text
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```
