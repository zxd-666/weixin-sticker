import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const source = readFileSync(new URL("../assets/表情包切割.html", import.meta.url), "utf8");
const start = source.indexOf("function boxDistance(");
const end = source.indexOf("function segmentStickers(", start);
assert.ok(start >= 0 && end > start);
const context = {};
vm.runInNewContext(source.slice(start, end) + "\nglobalThis.groupComponents = groupComponents;", context);

test("a detached decoration cluster rejoins the nearby sticker", () => {
  const components = [
    { label: 0, minX: 100, minY: 200, maxX: 300, maxY: 500, pixelCount: 50000 },
    { label: 1, minX: 380, minY: 180, maxX: 410, maxY: 210, pixelCount: 900 },
    { label: 2, minX: 340, minY: 190, maxX: 370, maxY: 220, pixelCount: 500 },
    { label: 3, minX: 305, minY: 210, maxX: 335, maxY: 240, pixelCount: 300 },
  ];
  const groups = context.groupComponents(components, 1000, 1000);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].labels.length, 4);
});

test("two similarly sized stickers remain separate", () => {
  const components = [
    { label: 0, minX: 100, minY: 200, maxX: 300, maxY: 500, pixelCount: 50000 },
    { label: 1, minX: 350, minY: 200, maxX: 550, maxY: 500, pixelCount: 49000 },
  ];
  assert.equal(context.groupComponents(components, 1000, 1000).length, 2);
});

test("sticker filenames accept safe names in any language or their position when blank", () => {
  const filenameStart = source.indexOf("function pieceFilename(");
  const filenameEnd = source.indexOf("window.emojiCutterCore", filenameStart);
  assert.ok(filenameStart >= 0 && filenameEnd > filenameStart);
  const filenameContext = {};
  vm.runInNewContext(source.slice(filenameStart, filenameEnd) + "\nglobalThis.pieceFilename = pieceFilename; globalThis.parseThemeList = parseThemeList;", filenameContext);
  assert.equal(filenameContext.pieceFilename("开心"), "开心.png");
  assert.equal(filenameContext.pieceFilename("Happy"), "Happy.png");
  assert.equal(filenameContext.pieceFilename("OK_2"), "OK_2.png");
  assert.equal(filenameContext.pieceFilename("🎉"), "🎉.png");
  assert.equal(filenameContext.pieceFilename("", 0), "1.png");
  assert.equal(filenameContext.pieceFilename("  ", 15), "16.png");
  assert.equal(filenameContext.pieceFilename("1"), "1.png");
  assert.throws(() => filenameContext.pieceFilename("a/b"), /禁用字符/);
  assert.throws(() => filenameContext.pieceFilename("CON"), /保留名称/);
  assert.throws(() => filenameContext.pieceFilename("a".repeat(41)), /40/);

  assert.deepEqual(Array.from(filenameContext.parseThemeList("主题：你好、Happy、🎉", 3)), ["你好", "Happy", "🎉"]);
  assert.deepEqual(Array.from(filenameContext.parseThemeList("你好、、点赞", 4)), ["你好", "", "点赞", ""]);
  assert.throws(() => filenameContext.parseThemeList("你好、开心、点赞", 2), /超过当前/);
  assert.throws(() => filenameContext.parseThemeList("你好、a/b", 2), /禁用字符/);
  assert.throws(() => filenameContext.parseThemeList("你好、你好", 2), /重复/);
});

test("deleting one result keeps the others in order and renumbers them", () => {
  const deleteStart = source.indexOf("function refreshResultOrder(");
  const deleteEnd = source.indexOf("function cropPointerPosition(", deleteStart);
  assert.ok(deleteStart >= 0 && deleteEnd > deleteStart);
  const makePiece = () => ({
    itemElement: { title: "", removed: false, remove() { this.removed = true; } },
    previewElement: { alt: "" },
    nameInput: { setAttribute() {} },
    deleteButton: { setAttribute() {} },
    cropButton: { setAttribute() {} },
  });
  const first = makePiece();
  const second = makePiece();
  const third = makePiece();
  const deletionContext = {
    pieces: [first, second, third],
    grid: { style: {} },
    resultTitle: { textContent: "" },
    downloadAll: { disabled: false },
    parseThemesButton: { disabled: false },
    parseStatus: { textContent: "" },
  };
  vm.runInNewContext(source.slice(deleteStart, deleteEnd) + "\nglobalThis.deletePiece = deletePiece;", deletionContext);
  deletionContext.deletePiece(second);
  assert.equal(deletionContext.pieces.length, 2);
  assert.equal(deletionContext.pieces[0], first);
  assert.equal(deletionContext.pieces[1], third);
  assert.equal(second.itemElement.removed, true);
  assert.equal(third.previewElement.alt, "第 2 张 240×240 表情");
  assert.equal(deletionContext.resultTitle.textContent, "切割结果 (2 张)");
  deletionContext.deletePiece(first);
  deletionContext.deletePiece(third);
  assert.equal(deletionContext.downloadAll.disabled, true);
  assert.equal(deletionContext.parseThemesButton.disabled, true);
});
