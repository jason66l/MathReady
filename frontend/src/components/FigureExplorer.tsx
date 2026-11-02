import { useState } from "react";
import type { FigurePart } from "../types";

interface Props {
  image: string;
  parts: FigurePart[];
  // When provided, labels and descriptions become editable (review screen).
  onChange?: (parts: FigurePart[]) => void;
  idPrefix: string;
}

function FigureExplorer({ image, parts, onChange, idPrefix }: Props) {
  // Which part is highlighted on the image (null = none).
  const [active, setActive] = useState<number | null>(null);

  function updatePart(index: number, changes: Partial<FigurePart>) {
    if (!onChange) return;
    onChange(parts.map((p, i) => (i === index ? { ...p, ...changes } : p)));
  }

  function removePart(index: number) {
    if (!onChange) return;
    onChange(parts.filter((_, i) => i !== index));
    setActive(null);
  }

  return (
    <div className="figure-explorer">
      <div className="figure-stage">
        <img src={image} alt="" />
        {parts.map((p, i) => (
          <div
            key={i}
            className={`part-box ${active === i ? "active" : ""}`}
            style={{
              left: `${p.box[0] * 100}%`,
              top: `${p.box[1] * 100}%`,
              width: `${(p.box[2] - p.box[0]) * 100}%`,
              height: `${(p.box[3] - p.box[1]) * 100}%`,
            }}
            aria-hidden="true"
          >
            <span className="part-number">{i + 1}</span>
          </div>
        ))}
      </div>

      {parts.length > 0 && (
        <>
          <p className="parts-heading">Diagram parts <span className="hint-inline">(found by SAM 3.1, hover or tab to highlight)</span></p>
          <ol className="part-list" onMouseLeave={() => setActive(null)}>
            {parts.map((p, i) => (
              <li
                key={i}
                className={active === i ? "active" : ""}
                onMouseEnter={() => setActive(i)}
                onFocus={() => setActive(i)}
              >
                <span className="part-index" aria-hidden="true">{i + 1}</span>
                <div className="part-fields">
                  {onChange ? (
                    <>
                      <label htmlFor={`${idPrefix}-part-${i}-label`}>Part {i + 1} name</label>
                      <input
                        id={`${idPrefix}-part-${i}-label`}
                        value={p.label}
                        onChange={(e) => updatePart(i, { label: e.target.value })}
                      />
                      <label htmlFor={`${idPrefix}-part-${i}-desc`}>Part {i + 1} description</label>
                      <textarea
                        id={`${idPrefix}-part-${i}-desc`}
                        rows={2}
                        value={p.description}
                        onChange={(e) => updatePart(i, { description: e.target.value })}
                      />
                      <button type="button" className="link-button" onClick={() => removePart(i)}>
                        Remove part {i + 1}
                      </button>
                    </>
                  ) : (
                    <button type="button" className="part-button">
                      <strong>{p.label}:</strong> {p.description}
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}

export default FigureExplorer;