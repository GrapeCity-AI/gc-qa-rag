# Cell Overflow

An explanation of what the cell overflow property does in SpreadJS

## Content

You can allow the text in a cell to overflow into an adjacent cell with the **options.allowCellOverflow** property.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/coverflow.png)

The following code sample sets the alignment and allows the text to overflow into other cells.

```javascript
activeSheet.options.allowCellOverflow = true;
activeSheet.getCell(0,3, GC.Spread.Sheets.SheetArea.viewport).hAlign(GC.Spread.Sheets.HorizontalAlign.left);
activeSheet.getCell(1,3, GC.Spread.Sheets.SheetArea.viewport).hAlign(GC.Spread.Sheets.HorizontalAlign.center);
activeSheet.getCell(2,3, GC.Spread.Sheets.SheetArea.viewport).hAlign(GC.Spread.Sheets.HorizontalAlign.right);
activeSheet.getCell(3,3, GC.Spread.Sheets.SheetArea.viewport).hAlign(GC.Spread.Sheets.HorizontalAlign.general);
activeSheet.getCell(0,3, GC.Spread.Sheets.SheetArea.viewport).text("Data overflows to the right");
activeSheet.getCell(1,3, GC.Spread.Sheets.SheetArea.viewport).text("Data overflows to the left and right");
activeSheet.getCell(2,3, GC.Spread.Sheets.SheetArea.viewport).text("Data overflows to the left");
```