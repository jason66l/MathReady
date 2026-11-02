import { useState } from "react";
import type { Block } from "../types";

interface Props {
  block: Block;
  onChange: (updated: Block) => void;
}

const STATUS_LABEL = {
  draft: "Draft",
  needs_review: "Needs review",
  approved: "Approved",
};

function BlockCard({ block, onChange }: Props) {
  // A private copy of the block that holds edits until Save or Approve is clicked.
  const [draft, setDraft] = useState<Block>(block);

  const changed = JSON.stringify(draft) !== JSON.stringify(block);
  const fieldId = (name: string) => `${block.id}-${name}`;

  function save(approve: boolean) {
    onChange({ ...draft, status: approve ? "approved" : draft.status });
  }

  return (
    <article id={block.id} className={`block ${block.status}`}>
      <p className="block-meta">
        <span className="block-type">{block.type}</span>
        <span className={`badge ${block.status}`}>{STATUS_LABEL[block.status]}</span>
        {block.confidence !== undefined && (
          <span>confidence {Math.round(block.confidence * 100)}%</span>
        )}
      </p>

      {block.error && <p className="error">{block.error}</p>}

      {/* Equations: rendered MathML + editable LaTeX */}
      {block.type === "equation" && (
        <>
          <div
            className="math-preview"
            // MathML comes from our own backend, so inserting it as HTML is safe here.
            dangerouslySetInnerHTML={{ __html: block.mathml ?? "" }}
          />
          <label htmlFor={fieldId("latex")}>LaTeX</label>
          <textarea
            id={fieldId("latex")}
            rows={2}
            value={draft.latex ?? ""}
            onChange={(e) => setDraft({ ...draft, latex: e.target.value })}
          />
        </>
      )}

      {/* Figures: image + alt text fields */}
      {block.type === "figure" && (
        <>
          {block.image ? (
            <img className="figure-crop" src={block.image} alt="" />
          ) : (
            <div className="placeholder small">Figure image will appear here</div>
          )}
          <label htmlFor={fieldId("short")}>Short alt text</label>
          <input
            id={fieldId("short")}
            value={draft.alt_short ?? ""}
            onChange={(e) => setDraft({ ...draft, alt_short: e.target.value })}
          />
          <p className="hint">{(draft.alt_short ?? "").length} characters (aim for under 150)</p>
          <label htmlFor={fieldId("long")}>Full description</label>
          <textarea
            id={fieldId("long")}
            rows={4}
            value={draft.alt_long ?? ""}
            onChange={(e) => setDraft({ ...draft, alt_long: e.target.value })}
          />
        </>
      )}

      {/* Tables: shown as a real table */}
      {block.type === "table" && (
        <table>
          {block.caption && <caption>{block.caption}</caption>}
          <thead>
            <tr>
              {(block.headers ?? []).map((h, i) => (
                <th key={i} scope="col">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(block.rows ?? []).map((row, r) => (
              <tr key={r}>
                {row.map((cell, c) => (
                  <td key={c}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Headings and paragraphs: editable text */}
      {(block.type === "heading" || block.type === "paragraph") && (
        <>
          <label htmlFor={fieldId("text")}>
            {block.type === "heading" ? `Heading (level ${block.level ?? 1})` : "Paragraph"}
          </label>
          <textarea
            id={fieldId("text")}
            rows={block.type === "heading" ? 1 : 3}
            value={draft.text ?? ""}
            onChange={(e) => setDraft({ ...draft, text: e.target.value })}
          />
        </>
      )}

      <div className="actions">
        <button className="secondary" disabled={!changed} onClick={() => save(false)}>
          Save
        </button>
        <button onClick={() => save(true)} disabled={block.status === "approved" && !changed}>
          {block.status === "approved" && !changed ? "Approved" : "Save and approve"}
        </button>
      </div>
    </article>
  );
}

export default BlockCard;