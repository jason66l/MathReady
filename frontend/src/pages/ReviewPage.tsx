import { useState } from "react";
import type { Block, Doc } from "../types";
import { mockDoc } from "../mock";
import BlockCard from "../components/BlockCard";

interface Props {
  docId: string;
}

function ReviewPage({ docId }: Props) {
  // For now every document is the mock. Later this loads from the backend by docId.
  const [doc, setDoc] = useState<Doc>(mockDoc);
  const [onlyFlagged, setOnlyFlagged] = useState(false);

  // Count blocks that still need a human to check them.
  const pending = doc.pages
    .flatMap((page) => page.blocks)
    .filter((block) => block.status === "needs_review").length;

  // Replace one block with an edited version, leaving everything else as is.
  function updateBlock(updated: Block) {
    setDoc((current) => ({
      ...current,
      pages: current.pages.map((page) => ({
        ...page,
        blocks: page.blocks.map((block) => (block.id === updated.id ? updated : block)),
      })),
    }));
  }

  return (
    <div className="review">
      <h1>{doc.title}</h1>

      <div className="toolbar" role="status" aria-live="polite">
        {pending > 0 ? (
          <p>
            <strong>{pending}</strong> item{pending === 1 ? "" : "s"} need your review before export.
          </p>
        ) : (
          <p>Everything is reviewed. Ready to export.</p>
        )}

        <label className="toggle">
          <input
            type="checkbox"
            checked={onlyFlagged}
            onChange={(e) => setOnlyFlagged(e.target.checked)}
          />
          Show only items needing review
        </label>

        <button disabled={pending > 0} onClick={() => alert(`Export ${docId}: coming soon`)}>
          Download accessible HTML
        </button>
      </div>

      {doc.pages.map((page) => {
        const blocks = onlyFlagged
          ? page.blocks.filter((b) => b.status === "needs_review")
          : page.blocks;
        if (blocks.length === 0) return null;

        return (
          <section key={page.n} className="page" aria-labelledby={`page-${page.n}`}>
            <h2 id={`page-${page.n}`}>Page {page.n}</h2>
            <div className="split">
              <div className="original">
                {page.image ? (
                  <img src={page.image} alt={`Original scan of page ${page.n}`} />
                ) : (
                  <div className="placeholder">Page image will appear here</div>
                )}
              </div>
              <div className="blocks">
                {blocks.map((block) => (
                  <BlockCard key={block.id} block={block} onChange={updateBlock} />
                ))}
              </div>
            </div>
          </section>
        );
      })}
    </div>
  );
}

export default ReviewPage;