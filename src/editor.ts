import { python } from "@codemirror/lang-python";
import { defaultKeymap, history, indentWithTab, redo, undo, undoDepth } from "@codemirror/commands";
import { bracketMatching, HighlightStyle, indentOnInput, indentUnit, syntaxHighlighting } from "@codemirror/language";
import { EditorState, Prec } from "@codemirror/state";
import { drawSelection, EditorView, highlightActiveLine, keymap, lineNumbers } from "@codemirror/view";
import { tags as t } from "@lezer/highlight";

const terminalTheme = EditorView.theme(
  {
    "&": { height: "100%", color: "var(--fg)", backgroundColor: "transparent" },
    ".cm-content": { caretColor: "var(--fg)", fontFamily: "var(--font)" },
    ".cm-scroller": { fontFamily: "var(--font)", lineHeight: "1.5" },
    ".cm-gutters": { backgroundColor: "transparent", color: "var(--dim)", border: "none" },
    ".cm-activeLine": { backgroundColor: "rgba(51, 255, 102, 0.06)" },
    ".cm-activeLineGutter": { backgroundColor: "transparent", color: "var(--fg)" },
    "&.cm-focused .cm-cursor": { borderLeft: "0.6em solid var(--fg)", animation: "blink 1s steps(1) infinite" },
    ".cm-selectionBackground, &.cm-focused .cm-selectionBackground": { backgroundColor: "rgba(51, 255, 102, 0.25) !important" },
    "&.cm-focused": { outline: "none" },
  },
  { dark: true },
);

const terminalHighlight = HighlightStyle.define([
  { tag: [t.keyword, t.controlKeyword, t.definitionKeyword], color: "#7dffa8", fontWeight: "bold" },
  { tag: [t.string], color: "var(--amber)" },
  { tag: [t.number, t.bool], color: "#ff9e4f" },
  { tag: [t.comment], color: "var(--dim)", fontStyle: "italic" },
  { tag: [t.function(t.definition(t.variableName))], color: "#b6ffcc", textDecoration: "underline" },
]);

export interface EditorOptions {
  doc: string;
  readOnly?: boolean;
  /** Undo する直前に呼ばれる。false を返すと Undo しない */
  onUndo?: () => boolean;
}

export function createEditor(parent: HTMLElement, opts: EditorOptions): EditorView {
  const undoGuard = Prec.highest(
    keymap.of([
      {
        key: "Mod-z",
        run: (v) => {
          if (undoDepth(v.state) > 0 && (opts.onUndo?.() ?? true)) undo(v);
          return true;
        },
      },
      { key: "Mod-y", run: redo },
      { key: "Mod-Shift-z", run: redo },
    ]),
  );
  return new EditorView({
    parent,
    state: EditorState.create({
      doc: opts.doc,
      extensions: [
        lineNumbers(),
        history(),
        drawSelection(),
        highlightActiveLine(),
        indentOnInput(),
        bracketMatching(),
        indentUnit.of("    "),
        python(),
        syntaxHighlighting(terminalHighlight),
        terminalTheme,
        undoGuard,
        // 右クリックメニュー等からの「元に戻す」は Undo 回数を素通りするので塞ぐ
        EditorView.domEventHandlers({
          beforeinput: (e) => {
            if (e.inputType !== "historyUndo" && e.inputType !== "historyRedo") return false;
            e.preventDefault();
            return true;
          },
        }),
        keymap.of([indentWithTab, ...defaultKeymap]),
        EditorState.readOnly.of(opts.readOnly ?? false),
      ],
    }),
  });
}

