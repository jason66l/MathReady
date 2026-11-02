import { useEffect, useState } from "react";
import type { Block } from "../types";
import type { BlockEdit } from "../api";

interface Props {
  block: Block;
  onSave: (edit: BlockEdit) => Promise<void>;
}

const STATUS_LABEL = {
  draft: "Draft",
  needs_review: "Needs review",
  approved: "Approved",
};

// The fields a reviewer can edit.
type Fields = Pick<Block, "text" | "latex" | "alt_short" | "alt_long">;

function fieldsOf(block: Block): Fields {
  return {
    text: block.text ?? "",
    latex: block.latex ?? "",
    alt_short: block.alt_short ?? "",
    alt_long: block.alt_long ?? "",
  };
}

function BlockCard({ block, onSave }: Props) {
  const [draft, setDraft] = useState<Fields>(fieldsOf(block));
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // When the backend sends back an updated block, reset the edit boxes to match it.
  useEffect(() => {
    setDraft(fieldsOf(block));
  }, [block]);

  // Only the fields that actually changed get sent.
  const original = fieldsOf(block);
  const edit: BlockEdit = {};
  (Object.keys(draft) as (keyof Fields)[]).forEach((key) => {
    if (draft[key] !== original[key]) edit[key] = draft[key];
  });
  const changed = Object.keys(edit).length > 0;

  async function save(approve: boolean) {
    setSaving(true);
    setSaveError(null);
    try {
      await onSave({ ...edit, approve });
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  const fieldId = (name: string) => `${block.id}-${name}`;
  const isApproved = block.status === "approved" && !changed;

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
            value={draft.latex}
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
            <div className="placeholder small">No figure image</div>
          )}
          <label htmlFor={fieldId("short")}>Short alt text</label>
          <input
            id={fieldId("short")}
            value={draft.alt_short}
            onChange={(e) => setDraft({ ...draft, alt_short: e.target.value })}
          />
          <p className="hint">{(draft.alt_short ?? "").length} characters (aim for under 150)</p>
          <label htmlFor={fieldId("long")}>Full description</label>
          <textarea
            id={fieldId("long")}
            rows={5}
            value={draft.alt_long}
            onChange={(e) => setDraft({ ...draft, alt_long: e.target.value })}
          />
        </>
      )}

      {/* Tables: real table with rendered math in cells */}
      {block.type === "table" && (
        <table>
          {block.caption && <caption>{block.caption}</caption>}
          <thead>
            <tr>
              {(block.headers_html ?? block.headers ?? []).map((h, i) => (
                <th key={i} scope="col" dangerouslySetInnerHTML={{ __html: h }} />
              ))}
            </tr>
          </thead>
          <tbody>
            {(block.rows_html ?? block.rows ?? []).map((row, r) => (
              <tr key={r}>
                {row.map((cell, c) => (
                  <td key={c} dangerouslySetInnerHTML={{ __html: cell }} />
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Headings and paragraphs: rendered preview + editable text */}
      {(block.type === "heading" || block.type === "paragraph") && (
        <>
          {block.html && (
            <p
              className={`text-preview ${block.type}`}
              dangerouslySetInnerHTML={{ __html: block.html }}
            />
          )}
          <label htmlFor={fieldId("text")}>
            {block.type === "heading" ? `Heading (level ${block.level ?? 1})` : "Paragraph"}
          </label>
          <textarea
            id={fieldId("text")}
            rows={block.type === "heading" ? 1 : 3}
            value={draft.text}
            onChange={(e) => setDraft({ ...draft, text: e.target.value })}
          />
        </>
      )}

      {saveError && <p className="error" role="alert">{saveError}</p>}

      <div className="actions">
        <button className="secondary" disabled={!changed || saving} onClick={() => save(false)}>
          Save
        </button>
        <button disabled={isApproved || saving} onClick={() => save(true)}>
          {saving ? "Saving..." : isApproved ? "Approved" : "Save and approve"}
        </button>
      </div>
    </article>
  );
}

export default BlockCard;