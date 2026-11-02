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
        <button className="brand" onClick={() => setDocId(null)}>
          MathReady
        </button>
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