import { useState } from "react";
import { uploadDocument } from "../api";

interface Props {
  // Called with the new document's id once the backend accepts the upload.
  onUploaded: (docId: string) => void;
}

function UploadPage({ onUploaded }: Props) {
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault(); // stop the browser from reloading the page

    if (!file) {
      setError("Choose a PDF file first.");
      return;
    }
    if (file.type !== "application/pdf") {
      setError("That file isn't a PDF.");
      return;
    }

    setError(null);
    setUploading(true);
    try {
      const docId = await uploadDocument(file, title);
      onUploaded(docId); // switch to the review screen
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="upload">
      <h1>Make STEM course materials accessible</h1>
      <p>
        Upload a PDF. MathReady turns equations into MathML that screen readers can
        navigate, and drafts descriptions for diagrams. You review everything before exporting.
      </p>

      <form onSubmit={handleSubmit} className="card" noValidate>
        <label htmlFor="title">Document title (optional)</label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Physics 7A - Problem Set 4"
        />

        <label htmlFor="file">PDF file</label>
        <input
          id="file"
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          aria-describedby={error ? "upload-error" : undefined}
        />

        {error && (
          <p id="upload-error" className="error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" disabled={uploading}>
          {uploading ? "Uploading..." : "Convert"}
        </button>
      </form>
    </section>
  );
}

export default UploadPage;