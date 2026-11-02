import { useEffect, useState } from "react";
import type { Block, Doc } from "../types";
import { exportUrl, getDocument, updateBlock, type BlockEdit } from "../api";
import BlockCard from "../components/BlockCard";

interface Props {
  docId: string;
}

function ReviewPage({ docId }: Props) {
  const [doc, setDoc] = useState<Doc | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [onlyFlagged, setOnlyFlagged] = useState(false);

  // Load the document, and keep reloading every 2 seconds while it's still processing.
  useEffect(() => {
    let stopped = false;
    let timer: number | undefined;

    async function load() {
      try {
        const latest = await getDocument(docId);
        if (stopped) return;
        setDoc(latest);
        setLoadError(null);
        if (latest.state === "processing") {
          timer = window.setTimeout(load, 2000);
        }
      } catch (err) {
        if (!stopped) setLoadError(err instanceof Error ? err.message : "Could not load document.");
      }
    }

    load();
    return () => {
      // Runs when leaving this screen: stop polling.
      stopped = true;
      window.clearTimeout(timer);
    };
  }, [docId]);

  // Send an edit to the backend, then swap the updated block into the page.
  async function saveBlock(blockId: string, edit: BlockEdit) {
    const updated: Block = await updateBlock(docId, blockId, edit);
    setDoc((current) =>
      current && {
        ...current,
        pages: current.pages.map((page) => ({
          ...page,
          blocks: page.blocks.map((block) => (block.id === blockId ? updated : block)),
        })),
      },
    );
  }

  if (loadError) {
    return <p className="error" role="alert">{loadError}</p>;
  }
  if (!doc) {
    return <p role="status">Loading...</p>;
  }

  const pending = doc.pages
    .flatMap((page) => page.blocks)
    .filter((block) => block.status === "needs_review").length;
  const processing = doc.state === "processing";

  return (
    <div className="review">
      <h1>{doc.title}</h1>

      <div className="toolbar" role="status" aria-live="polite">
        {processing ? (
          <p>
            <span className="spinner" aria-hidden="true" /> {doc.progress}
          </p>
        ) : doc.state === "error" ? (
          <p className="error">{doc.progress}</p>
        ) : pending > 0 ? (
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

        {processing || pending > 0 ? (
          <button disabled>Download accessible HTML</button>
        ) : (
          <a className="button" href={exportUrl(docId)}>
            Download accessible HTML
          </a>
        )}
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
                <img src={page.image} alt={`Original scan of page ${page.n}`} />
              </div>
              <div className="blocks">
                {blocks.map((block) => (
                  <BlockCard
                    key={block.id}
                    block={block}
                    onSave={(edit) => saveBlock(block.id, edit)}
                  />
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