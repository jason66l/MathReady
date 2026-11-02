import type { Block, Doc } from "./types";

// Turn a failed response into a readable error message.
async function check(res: Response): Promise<Response> {
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body.detail) message = body.detail;
    } catch {
      // response wasn't JSON; keep the status text
    }
    throw new Error(message);
  }
  return res;
}

// Upload a PDF. Returns the new document's id.
export async function uploadDocument(file: File, title: string): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  const res = await check(await fetch("/api/documents", { method: "POST", body: form }));
  const data = await res.json();
  return data.doc_id;
}

// Get the whole document (state, progress, pages, blocks).
export async function getDocument(docId: string): Promise<Doc> {
  const res = await check(await fetch(`/api/documents/${docId}`));
  return res.json();
}

// Fields the review screen can send when saving a block.
export interface BlockEdit {
  text?: string;
  latex?: string;
  alt_short?: string;
  alt_long?: string;
  approve?: boolean;
}

// Save edits and/or approve one block. Returns the updated block.
export async function updateBlock(docId: string, blockId: string, edit: BlockEdit): Promise<Block> {
  const res = await check(
    await fetch(`/api/documents/${docId}/blocks/${blockId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(edit),
    }),
  );
  return res.json();
}

// Link that downloads the accessible HTML.
export function exportUrl(docId: string): string {
  return `/api/documents/${docId}/export`;
}