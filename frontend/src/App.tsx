import { useState } from "react";
import UploadPage from "./pages/UploadPage";
import ReviewPage from "./pages/ReviewPage";

function App() {
  // The id of the document being reviewed, or null if none is open yet.
  const [docId, setDocId] = useState<string | null>(null);

  return (
    <>
      <a className="skip-link" href="#main">Skip to main content</a>
      <header className="app-header">
        <div className="app-header-inner">
          <button className="brand" onClick={() => setDocId(null)} aria-label="MathReady, back to upload">
            <span className="brand-mark" aria-hidden="true">∑</span>
            <span className="brand-name">MathReady</span>
          </button>
          <nav aria-label="Main">
            <ul className="nav">
              <li>
                <button
                  className={`nav-item ${docId === null ? "active" : ""}`}
                  aria-current={docId === null ? "page" : undefined}
                  onClick={() => setDocId(null)}
                >
                  Upload
                </button>
              </li>
              <li>
                <button
                  className={`nav-item ${docId !== null ? "active" : ""}`}
                  aria-current={docId !== null ? "page" : undefined}
                  disabled={docId === null}
                >
                  Review
                </button>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main id="main">
        {docId === null ? (
          <UploadPage onUploaded={(id) => setDocId(id)} />
        ) : (
          <ReviewPage docId={docId} />
        )}
      </main>
    </>
  );
}

export default App;