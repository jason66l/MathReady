import { useEffect, useState } from "react";
import type { Block, Doc } from "../types";
import { exportUrl, getDocument, updateBlock, type BlockEdit } from "../api";
import BlockCard from "../components/BlockCard";

interface Props {
  docId: string;
}

// "Reading page 2 of 5" -> 0.2 (used only to draw the progress bar)
function progressFraction(progress: string): number | null {
  const match = progress.match(/page (\d+) of (\d+)/i);
  if (!match) return null;
  const [current, total] = [Number(match[1]), Number(match[2])];
  return total > 0 ? Math.min(1, (current - 1) / total) : null;
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
    return <p className="alert alert-error" role="alert">{loadError}</p>;
  }
  if (!doc) {
    return (
      <p className="loading" role="status">
        <span className="spinner" aria-hidden="true" /> Loading document...
      </p>
    );
  }

  const allBlocks = doc.pages.flatMap((page) => page.blocks);
  const pending = allBlocks.filter((block) => block.status === "needs_review").length;
  const approved = allBlocks.filter((block) => block.status === "approved").length;
  const processing = doc.state === "processing";
  const fraction = processing ? progressFraction(doc.progress) : null;

  return (
    <div className="review">
      <div className="review-header">
        <div>
          <p className="eyebrow">Review</p>
          <h1>{doc.title}</h1>
        </div>
        <p className="review-stats">
          {doc.pages.length} page{doc.pages.length === 1 ? "" : "s"} · {allBlocks.length} items · {approved} approved
        </p>
      </div>

      <div className="toolbar">
        <div className="toolbar-status" role="status" aria-live="polite">
          {processing ? (
            <div className="progress">
              <p>
                <span className="spinner" aria-hidden="true" /> {doc.progress}
              </p>
              <div className="progress-track" aria-hidden="true">
                <div
                  className={`progress-fill ${fraction === null ? "indeterminate" : ""}`}
                  style={fraction === null ? undefined : { width: `${Math.max(6, fraction * 100)}%` }}
                />
              </div>
            </div>
          ) : doc.state === "error" ? (
            <p className="status-pill error">{doc.progress}</p>
          ) : pending > 0 ? (
            <p className="status-pill warning">
              <strong>{pending}</strong> item{pending === 1 ? "" : "s"} need your review before export
            </p>
          ) : (
            <p className="status-pill success">Everything is reviewed. Ready to export.</p>
          )}
        </div>

        <label className="toggle">
          <input
            type="checkbox"
            checked={onlyFlagged}
            onChange={(e) => setOnlyFlagged(e.target.checked)}
          />
          <span>Only show items needing review</span>
        </label>

        {processing || pending > 0 ? (
          <button className="primary-action" disabled>
            Download accessible HTML
          </button>
        ) : (
          <a className="button primary-action" href={exportUrl(docId)}>
            Download accessible HTML
          </a>
        )}
      </div>

      {onlyFlagged && pending === 0 && !processing && (
        <p className="empty-state">Nothing left to review. Every flagged item has been approved.</p>
      )}

      {doc.pages.map((page) => {
        const blocks = onlyFlagged
          ? page.blocks.filter((b) => b.status === "needs_review")
          : page.blocks;
        if (blocks.length === 0) return null;

        return (
          <section key={page.n} className="page" aria-labelledby={`page-${page.n}`}>
            <h2 id={`page-${page.n}`} className="page-title">Page {page.n}</h2>
            <div className="split">
              <div className="panel panel-original">
                <p className="panel-label">Original PDF</p>
                <img src={page.image} alt={`Original scan of page ${page.n}`} />
              </div>
              <div className="panel panel-blocks">
                <p className="panel-label">
                  Accessible version <span className="panel-count">{blocks.length} items</span>
                </p>
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