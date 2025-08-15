# Cell Span

A tutorial showing how to add and remove cell spans in a worksheet in SpreadJS

## Content

You can create a cell span in the cell, row header, or column header area by using the [addSpan](gcdocsite__documentlink?toc-item-id=995f2b70-17d8-47a4-8e09-962f84b4dfc1#addSpan) method. You can also clear cell spans using the [removeSpan](gcdocsite__documentlink?toc-item-id=995f2b70-17d8-47a4-8e09-962f84b4dfc1#removeSpan) method.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/cspan.png)

The entire span is treated as an active cell when using the Tab key to move the active cell to the spanned cell. The active cell outline includes the entire span.

The following code sample creates a span in the header and data areas.

```javascript
activeSheet.setRowCount(4,1);
activeSheet.setColumnCount(4,2);
activeSheet.addSpan(0,0,3,3,GC.Spread.Sheets.SheetArea.colHeader);
activeSheet.addSpan(0,0,3,3,GC.Spread.Sheets.SheetArea.rowHeader);
activeSheet.addSpan(0,0,3,3,GC.Spread.Sheets.SheetArea.viewport);
```

You can also bind blocks of cells by merging them as shown in the image below.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/codecellspan.png)

```javascript
window.onload = function()
{
   var spread = new GC.Spread.Sheets.Workbook(document.getElementById("ss"),{sheetCount:3});
   var activeSheet = spread.getActiveSheet();

   // Merge three columns with origin at cell(1,1).
   activeSheet.addSpan(1, 1, 1, 3, GC.Spread.Sheets.SheetArea.viewport);

   // Merge 2 rows x 2 columns with origin at cell(3,3).
   activeSheet.addSpan(3, 3, 2, 2, GC.Spread.Sheets.SheetArea.viewport);

   // Set on every anchor cell
   var cell = activeSheet.getCell(1, 1, GC.Spread.Sheets.SheetArea.viewport);
   cell.backColor("LightCyan");
   cell.value("Row binding");
   cell = activeSheet.getCell(3, 3, GC.Spread.Sheets.SheetArea.viewport);
   cell.backColor("LightPink");
   cell.value("Matrix binding");
   cell.hAlign(GC.Spread.Sheets.HorizontalAlign.center);
   cell.vAlign(GC.Spread.Sheets.VerticalAlign.center);
} 
```