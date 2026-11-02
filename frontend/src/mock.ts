import type { Doc } from "./types";

// Sample document matching what the backend will return for ps4.pdf.
// Used to build the UI before the backend exists.
export const mockDoc: Doc = {
  doc_id: "mock",
  title: "Physics 7A - Problem Set 4",
  state: "ready",
  progress: "Done",
  pages: [
    {
      n: 1,
      image: "",
      blocks: [
        { id: "p1b1", type: "heading", level: 1, status: "draft", text: "1. Block on an incline" },
        {
          id: "p1b2",
          type: "paragraph",
          status: "draft",
          text: "A block of mass \\(m = 2.0\\,\\text{kg}\\) rests on a frictionless ramp inclined at angle \\(\\theta = 30^\\circ\\).",
        },
        {
          id: "p1b3",
          type: "figure",
          status: "needs_review",
          image: "",
          alt_short: "Free-body diagram of a block on a frictionless incline.",
          alt_long:
            "A block of mass m sits on a ramp rising to the right at angle theta. Three forces act on it: the normal force N points up and away from the ramp surface, gravity mg points straight down, and the parallel component F points down the slope.",
        },
        {
          id: "p1b4",
          type: "equation",
          status: "draft",
          display: true,
          confidence: 0.99,
          latex: "a = g \\sin \\theta",
          mathml:
            '<math display="block"><mi>a</mi><mo>=</mo><mi>g</mi><mi>sin</mi><mi>θ</mi></math>',
        },
        {
          id: "p1b5",
          type: "equation",
          status: "needs_review",
          display: true,
          confidence: 0.72,
          latex: "\\int_0^{\\pi} x^2 \\sin x \\, dx",
          mathml:
            '<math display="block"><msubsup><mo>∫</mo><mn>0</mn><mi>π</mi></msubsup><msup><mi>x</mi><mn>2</mn></msup><mi>sin</mi><mi>x</mi><mspace width="0.167em"></mspace><mi>d</mi><mi>x</mi></math>',
        },
      ],
    },
    {
      n: 2,
      image: "",
      blocks: [
        { id: "p2b1", type: "heading", level: 1, status: "draft", text: "3. Measured data" },
        {
          id: "p2b2",
          type: "table",
          status: "draft",
          caption: "Position of the cart over time",
          headers: ["Time \\(t\\) (s)", "Position \\(x\\) (m)", "Uncertainty \\(\\sigma_x\\) (m)"],
          rows: [
            ["0.0", "0.00", "0.01"],
            ["0.5", "0.31", "0.01"],
            ["1.0", "1.22", "0.02"],
          ],
        },
        {
          id: "p2b3",
          type: "equation",
          status: "draft",
          display: true,
          confidence: 0.97,
          latex: "v = \\sqrt{2 g d \\sin \\theta}",
          mathml:
            '<math display="block"><mi>v</mi><mo>=</mo><msqrt><mn>2</mn><mi>g</mi><mi>d</mi><mi>sin</mi><mi>θ</mi></msqrt></math>',
        },
      ],
    },
  ],
};