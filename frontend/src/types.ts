// The kinds of content Muse Spark finds on a page.
export type BlockType = "heading" | "paragraph" | "equation" | "figure" | "table";

// Review state. Export is blocked while any block is "needs_review".
export type BlockStatus = "draft" | "needs_review" | "approved";

// One part of a figure, found by SAM 3.1 and described by Muse Spark.
export interface FigurePart {
  label: string;            // e.g. "Normal force N"
  description: string;      // e.g. "Arrow pointing up and away from the ramp"
  kind: string;             // what SAM searched for, e.g. "arrow"
  box: number[];            // [left, top, right, bottom] as 0-1 fractions of the image
}

// One piece of a page: a heading, paragraph, equation, figure or table.
export interface Block {
  id: string;               // e.g. "p1b3" = page 1, block 3
  type: BlockType;
  status: BlockStatus;
  error?: string | null;    // e.g. "LaTeX could not be converted"

  // heading + paragraph
  text?: string;            // may contain inline math as \( ... \)
  html?: string;            // the same text with inline math rendered (from backend)
  level?: number;           // heading level, 1-3

  // equation
  latex?: string;           // what Muse Spark read
  speech?: string;          // plain-English reading for screen readers
  mathml?: string;          // what screen readers navigate
  display?: boolean;        // true = its own line, false = inline
  confidence?: number;      // 0-1, how sure the model was

  // figure
  image?: string;           // URL of the cropped figure image
  alt_short?: string;       // one-sentence alt text
  alt_long?: string;        // full description
  parts?: FigurePart[];     // explorable parts (SAM 3.1 boxes + descriptions)

  // table
  caption?: string;
  headers?: string[];
  rows?: string[][];
  headers_html?: string[];  // headers with inline math rendered (from backend)
  rows_html?: string[][];   // cells with inline math rendered (from backend)
}

// One PDF page and the blocks found on it.
export interface Page {
  n: number;                // page number, starting at 1
  image: string;            // URL of the rendered page image
  blocks: Block[];
}

// A whole uploaded document.
export interface Doc {
  doc_id: string;
  title: string;
  state: "processing" | "ready" | "error";
  progress: string;         // e.g. "Reading page 2 of 5"
  pages: Page[];
}