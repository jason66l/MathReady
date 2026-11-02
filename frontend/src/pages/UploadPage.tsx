import { useState } from "react";
import { uploadDocument } from "../api";

interface Props {
  // Called with the new document's id once the backend accepts the upload.
  onUploaded: (docId: string) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function UploadPage({ onUploaded }: Props) {
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);

  function chooseFile(chosen: File | null) {
    setFile(chosen);
    setError(null);
  }

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
      <p className="eyebrow">For STEM instructors</p>
      <h1>Make your course materials accessible</h1>
      <p className="lede">
        Upload a PDF of lecture notes or a problem set. MathReady turns equations into math
        screen readers can navigate and drafts descriptions for diagrams. You review everything
        before exporting.
      </p>

      <form onSubmit={handleSubmit} className="upload-card" noValidate>
        <label
          htmlFor="file"
          className={`dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            chooseFile(e.dataTransfer.files?.[0] ?? null);
          }}
        >
          <svg className="dropzone-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
            <path d="M14 3v5h5" />
            <path d="M12 17v-6" />
            <path d="m9.5 13.5 2.5-2.5 2.5 2.5" />
          </svg>
          {file ? (
            <>
              <span className="dropzone-title">{file.name}</span>
              <span className="dropzone-hint">{formatSize(file.size)} · Click or drop to replace</span>
            </>
          ) : (
            <>
              <span className="dropzone-title">
                {dragging ? "Drop your PDF here" : "Drag a PDF here, or click to browse"}
              </span>
              <span className="dropzone-hint">Typed or handwritten, up to 30 pages</span>
            </>
          )}
          <input
            id="file"
            className="visually-hidden"
            type="file"
            accept="application/pdf"
            onChange={(e) => chooseFile(e.target.files?.[0] ?? null)}
            aria-describedby={error ? "upload-error" : undefined}
          />
        </label>

        <label htmlFor="title">Document title <span className="optional">(optional)</span></label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Physics 7A, Problem Set 4"
        />

        {error && (
          <p id="upload-error" className="alert alert-error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="primary-action" disabled={uploading}>
          {uploading ? "Uploading..." : "Convert to accessible HTML"}
        </button>
      </form>

      <ol className="how-it-works" aria-label="How it works">
        <li><span className="step-num" aria-hidden="true">1</span> Upload a PDF</li>
        <li><span className="step-num" aria-hidden="true">2</span> Review flagged equations and diagrams</li>
        <li><span className="step-num" aria-hidden="true">3</span> Download one accessible HTML file</li>
      </ol>
    </section>
  );
}

export default UploadPage;