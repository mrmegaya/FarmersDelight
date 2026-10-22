// Renders content.js to FarmersDelight_BRD_PRD_v2.0.docx and to BRD.md / PRD.md
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Header, Footer, AlignmentType,
  LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak, VerticalAlign, PageOrientation,
  TableOfContents,
} = require("docx");
const C = require("./content.js");
const OUT = process.argv[2] || ".";

const GREEN = "2F7D3B", DARK = "1F5C2A", LIGHT = "E6F2E4", AMBER = "B8690A", INK = "1E2A22", MUTED = "5F6B62", LINE = "D9DED3";
const FONT = "Arial";
const PW = 9638, LW = 14400; // content widths: A4 portrait (2 cm margins), A4 landscape (1.5 cm margins)

const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 21, bold: o.bold, italics: o.italic, color: o.color || INK });
const para = (text, o = {}) => new Paragraph({ spacing: { after: o.after ?? 120, line: 288 }, alignment: o.align, children: [run(text, o)] });
const bd = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
const scale = (widths, W) => { const s = widths.reduce((a, b) => a + b, 0); const w = widths.map((x) => Math.floor(x * W / s)); w[w.length - 1] += W - w.reduce((a, b) => a + b, 0); return w; };
const cell = (text, width, o = {}) => new TableCell({
  width: { size: width, type: WidthType.DXA }, borders, verticalAlign: VerticalAlign.TOP,
  shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
  margins: { top: 70, bottom: 70, left: 110, right: 110 },
  children: [new Paragraph({ spacing: { after: 20, line: 264 }, children: [new TextRun({ text: String(text), font: FONT, size: 18, bold: o.bold, color: o.color || INK })] })],
});
const mkTable = (b, W) => {
  const widths = scale(b.widths, W);
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: b.header.map((t, i) => cell(t, widths[i], { fill: GREEN, bold: true, color: "FFFFFF" })) }),
      ...b.rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((t, i) => cell(t, widths[i], { fill: ri % 2 ? "F5F7F2" : undefined, bold: i === 0 })) })),
    ],
  });
};
const callout = (title, text, W) => new Table({
  width: { size: W, type: WidthType.DXA }, columnWidths: [W],
  rows: [new TableRow({ children: [new TableCell({
    width: { size: W, type: WidthType.DXA },
    borders: { top: bd, bottom: bd, right: bd, left: { style: BorderStyle.SINGLE, size: 24, color: GREEN } },
    shading: { fill: LIGHT, type: ShadingType.CLEAR, color: "auto" }, margins: { top: 100, bottom: 100, left: 160, right: 160 },
    children: [new Paragraph({ spacing: { after: 40 }, children: [run(title, { bold: true, color: DARK, size: 20 })] }),
      new Paragraph({ spacing: { after: 0, line: 276 }, children: [run(text, { size: 19 })] })],
  })] })],
});
const gap = () => new Paragraph({ spacing: { after: 100 }, children: [] });

function docxBlocks(blocks, W) {
  const out = [];
  for (const b of blocks) {
    switch (b.type) {
      case "part":
        out.push(new Paragraph({ spacing: { after: 60 }, children: [run(b.label, { bold: true, color: AMBER, size: 20 })] }));
        out.push(new Paragraph({ spacing: { after: 200 }, children: [run(b.title, { bold: true, color: DARK, size: 40 })] }));
        break;
      case "h1": out.push(new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 140 }, keepNext: true, children: [new TextRun({ text: b.text, font: FONT, size: 30, bold: true, color: DARK })], border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: GREEN, space: 4 } } })); break;
      case "h2": out.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 100 }, keepNext: true, children: [new TextRun({ text: b.text, font: FONT, size: 24, bold: true, color: GREEN })] })); break;
      case "h3": out.push(new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 160, after: 60 }, keepNext: true, children: [new TextRun({ text: b.text, font: FONT, size: 22, bold: true, color: INK })] })); break;
      case "p": out.push(para(b.text, { italic: b.italic, color: b.italic ? MUTED : INK })); break;
      case "bullets": b.items.forEach((t) => out.push(new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 }, children: [run(t)] }))); break;
      case "numbered": {
        const ref = "num" + (docxBlocks.n = (docxBlocks.n || 0) + 1);
        docxBlocks.refs.push(ref);
        b.items.forEach((t) => out.push(new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 60, line: 276 }, children: [run(t)] })));
        break;
      }
      case "table": out.push(mkTable(b, W), gap()); break;
      case "callout": out.push(callout(b.title, b.text, W), gap()); break;
      case "pagebreak": out.push(new Paragraph({ children: [new PageBreak()] })); break;
      case "image": {
        const data = fs.readFileSync(C.IMG + b.file);
        const w = 880, h = Math.round(w * 2480 / 3508);
        if (out.imgCount) out.push(new Paragraph({ children: [new PageBreak()] }));
        out.imgCount = (out.imgCount || 0) + 1;
        out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 }, keepNext: true, children: [new ImageRun({ type: "png", data, transformation: { width: w, height: h }, altText: { title: b.caption, description: b.caption, name: b.file } })] }));
        out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 }, children: [run(b.caption, { bold: true, color: MUTED, size: 19 })] }));
        break;
      }
    }
  }
  return out;
}
docxBlocks.refs = [];

// split into sections by orientation markers
const sections = [];
let cur = { orient: "portrait", blocks: [] };
for (const b of C.blocks) {
  if (b.type === "landscape" || b.type === "portrait") { sections.push(cur); cur = { orient: b.type, blocks: [] }; }
  else cur.blocks.push(b);
}
sections.push(cur);

const header = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [run(`FarmersDelight · BRD and PRD · v${C.meta.version}`, { size: 16, color: MUTED })] })] });
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
  new TextRun({ text: "Page ", font: FONT, size: 16, color: MUTED }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: MUTED }),
  new TextRun({ text: " of ", font: FONT, size: 16, color: MUTED }), new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: MUTED })] })] });

const cover = [
  new Paragraph({ spacing: { before: 1800, after: 120 }, children: [new TextRun({ text: "FARMERSDELIGHT", font: FONT, size: 24, bold: true, color: AMBER, characterSpacing: 60 })] }),
  new Paragraph({ spacing: { after: 160 }, children: [run(C.meta.subtitle, { bold: true, color: DARK, size: 56 })] }),
  new Paragraph({ spacing: { after: 360 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: GREEN, space: 10 } }, children: [run(C.meta.docname, { color: MUTED, size: 28 })] }),
  mkTable(C.coverTable, PW), gap(),
  new Paragraph({ spacing: { after: 80 }, children: [run("Revision history", { bold: true, color: DARK, size: 24 })] }),
  mkTable(C.revisions, PW),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ spacing: { after: 160 }, children: [run("Contents", { bold: true, color: DARK, size: 32 })] }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ spacing: { before: 120 }, children: [run("Right-click the table and choose Update Field to refresh page numbers.", { italic: true, color: MUTED, size: 17 })] }),
  new Paragraph({ children: [new PageBreak()] }),
];

const docSections = sections.filter((s) => s.blocks.length).map((s, i) => {
  const land = s.orient === "landscape";
  const W = land ? LW : PW;
  return {
    properties: { page: { size: { width: 11906, height: 16838, orientation: land ? PageOrientation.LANDSCAPE : PageOrientation.PORTRAIT },
      margin: land ? { top: 850, bottom: 850, left: 850, right: 850 } : { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    headers: { default: header }, footers: { default: footer },
    children: [...(i === 0 ? cover : []), ...docxBlocks(s.blocks, W)],
  };
});

const doc = new Document({
  creator: "FarmersDelight", title: "FarmersDelight BRD and PRD v" + C.meta.version,
  styles: { default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, font: FONT, color: DARK }, paragraph: { outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, font: FONT, color: GREEN }, paragraph: { outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 22, bold: true, font: FONT }, paragraph: { outlineLevel: 2 } },
    ] },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    ...Array.from({ length: 12 }, (_, k) => ({ reference: "num" + (k + 1), levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] })),
  ] },
  features: { updateFields: true },
  sections: docSections,
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(path.join(OUT, "FarmersDelight_BRD_PRD_v2.0.docx"), buf);
  console.log("docx written", buf.length);
});

// ---------------------------------------------------------------- Markdown
const esc = (s) => String(s).replace(/\|/g, "\\|");
function md(blocks, imgPrefix) {
  let s = "", n = 0;
  for (const b of blocks) {
    switch (b.type) {
      case "part": s += `\n# ${b.title}\n\n`; break;
      case "h1": s += `\n## ${b.text}\n\n`; break;
      case "h2": s += `\n### ${b.text}\n\n`; break;
      case "h3": s += `\n#### ${b.text}\n\n`; break;
      case "p": s += (b.italic ? `*${b.text}*` : b.text) + "\n\n"; break;
      case "bullets": s += b.items.map((t) => `- ${t}`).join("\n") + "\n\n"; break;
      case "numbered": s += b.items.map((t, i) => `${i + 1}. ${t}`).join("\n") + "\n\n"; break;
      case "table": s += `| ${b.header.map(esc).join(" | ")} |\n| ${b.header.map(() => "---").join(" | ")} |\n` + b.rows.map((r) => `| ${r.map(esc).join(" | ")} |`).join("\n") + "\n\n"; break;
      case "callout": s += `> **${b.title}**  \n> ${b.text}\n\n`; break;
      case "image": s += `**${b.caption}**\n\n![${b.caption}](${imgPrefix}${b.file})\n\n`; break;
    }
  }
  return s;
}
const head = (name) => `<!-- Generated from docs/source/content.js — edit there and run build.js -->\n# FarmersDelight — ${name}\n\nVersion ${C.meta.version} · ${C.meta.date} · Word version: [FarmersDelight_BRD_PRD_v2.0.docx](FarmersDelight_BRD_PRD_v2.0.docx)\n\n`;
const iPart = C.blocks.findIndex((b) => b.type === "part" && b.label === "PART B");
const brdMd = head("Business Requirements Document (BRD)") + md([{ type: "table", ...C.coverTable }, { type: "h1", text: "Revision history" }, { type: "table", ...C.revisions }], "") + md(C.blocks.slice(1, iPart - 1), "../designs/");
const prdMd = head("Product Requirements Document (PRD)") + md(C.blocks.slice(iPart + 1), "../designs/");
fs.writeFileSync(path.join(OUT, "BRD.md"), brdMd);
fs.writeFileSync(path.join(OUT, "PRD.md"), prdMd);
console.log("markdown written");
