# Cell Padding and Label Styles

A tutorial showing how to use cell padding and label styles in SpreadJS, including watermarks, fonts, forecolor, alignment, and visibility

## Content

You can set cell padding and other style options for a watermark. You can set styles such as font, forecolor, alignment, and visibility.

Use the [cellPadding](gcdocsite__documentlink?toc-item-id=1a4e9265-6694-48bb-b0fc-15e5ab238a26#cellPadding) field to set cell padding and style options.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/cellpadding.png)

The following code sample adds watermarks to cells and sets the padding and other style options.

```javascript
var type = new GC.Spread.Sheets.Style();
type.watermark = "User name";
type.cellPadding = "20";
type.labelOptions = {alignment:GC.Spread.Sheets.LabelAlignment.topLeft, visibility: GC.Spread.Sheets.LabelVisibility.visible};

activeSheet.setStyle(0, 1, type);
activeSheet.getRange(0, -1, 1, -1, GC.Spread.Sheets.SheetArea.viewport).height(60);
activeSheet.getRange(-1, 1, -1, 1).width(150);

var combo = new GC.Spread.Sheets.CellTypes.ComboBox();
combo.items([{ text: "Oranges", value: "11k" }, { text: "Apples", value: "15k" }, { text: "Grape", value: "100k" }]);
combo.editorValueType(GC.Spread.Sheets.CellTypes.EditorValueType.text);

activeSheet.setCellType(2, 1, combo, GC.Spread.Sheets.SheetArea.viewport);
activeSheet.getCell(2, 1, GC.Spread.Sheets.SheetArea.viewport).watermark("ComboBox Cell Type").cellPadding('10 10 20 10');
activeSheet.getCell(2, 1, GC.Spread.Sheets.SheetArea.viewport).labelOptions({alignment: GC.Spread.Sheets.LabelAlignment.bottomCenter, foreColor: 'yellowgreen', font: 'bold 15px Arial'});
activeSheet.getRange(2, -1, 1, -1, GC.Spread.Sheets.SheetArea.viewport).height(60);
```